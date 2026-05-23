"""CLI command: route log entries to stdout sinks based on level or keyword."""
from __future__ import annotations

import sys
from typing import List

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.log_parser import LogEntry, parse_line
from logslice.router import Route, Router
from logslice.highlighter import format_entry


def _make_sink(label: str, use_color: bool) -> callable:
    def _sink(entry: LogEntry) -> None:
        prefix = click.style(f"[{label}]", fg="magenta", bold=True) if use_color else f"[{label}]"
        click.echo(f"{prefix} {format_entry(entry, term=None, use_color=use_color)}")
    return _sink


@click.command("route")
@click.argument("container")
@click.option("--route", "rules", multiple=True, metavar="LABEL:PATTERN",
              help="Routing rule in NAME:KEYWORD format. Repeatable.")
@click.option("--level-route", "level_rules", multiple=True, metavar="LABEL:LEVEL",
              help="Route by log level, e.g. errors:error.")
@click.option("--stop", is_flag=True, default=False,
              help="Stop evaluating further routes after first match.")
@click.option("--tail", default=100, show_default=True, help="Number of recent lines.")
@click.option("--no-color", is_flag=True, default=False)
def route_command(
    container: str,
    rules: List[str],
    level_rules: List[str],
    stop: bool,
    tail: int,
    no_color: bool,
) -> None:
    """Stream logs from CONTAINER and dispatch entries to labelled sinks."""
    use_color = not no_color
    router = Router()

    for rule in rules:
        if ":" not in rule:
            raise click.BadParameter(f"Invalid rule '{rule}', expected LABEL:PATTERN")
        label, pattern = rule.split(":", 1)
        p = pattern.lower()
        router.add_route(Route(
            name=label,
            match=lambda e, _p=p: _p in e.message.lower(),
            sink=_make_sink(label, use_color),
            stop=stop,
        ))

    for rule in level_rules:
        if ":" not in rule:
            raise click.BadParameter(f"Invalid level rule '{rule}', expected LABEL:LEVEL")
        label, lvl = rule.split(":", 1)
        lvl_lower = lvl.lower()
        router.add_route(Route(
            name=label,
            match=lambda e, _l=lvl_lower: (e.level or "").lower() == _l,
            sink=_make_sink(label, use_color),
            stop=stop,
        ))

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if entry:
                router.dispatch(entry)
    except DockerClientError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
