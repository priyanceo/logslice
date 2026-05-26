"""CLI command: logslice tail — live-tail a container's logs."""
from __future__ import annotations

import click

from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.log_parser import parse_line
from logslice.filter_engine import build_filter_chain, apply
from logslice.highlighter import format_entry
from logslice.tailer import Tailer, TailerError


@click.command("tail")
@click.argument("container")
@click.option("--backfill", default=0, show_default=True,
              help="Emit the last N buffered lines before live output.")
@click.option("--level", default=None, help="Filter by log level (e.g. ERROR).")
@click.option("--search", default=None, help="Fuzzy search term.")
@click.option("--no-color", is_flag=True, default=False, help="Disable ANSI colours.")
def tail_command(
    container: str,
    backfill: int,
    level: str | None,
    search: str | None,
    no_color: bool,
) -> None:
    """Live-tail logs from CONTAINER with optional backfill and filtering."""
    try:
        tailer = Tailer(backfill=backfill)
    except TailerError as exc:
        raise click.ClickException(str(exc)) from exc

    filters = build_filter_chain(level=level, search=search)

    try:
        client = DockerLogClient()
        raw_stream = client.stream_logs(container, tail=max(backfill, 0))
        entries = (parse_line(line) for line in raw_stream)
        for entry in tailer.feed(entries):
            if apply(filters, entry):
                click.echo(format_entry(entry, colorize=not no_color))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
