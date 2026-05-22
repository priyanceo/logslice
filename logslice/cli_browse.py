"""CLI entry point: logslice browse — stream and highlight logs from a container."""

from __future__ import annotations

import sys
from typing import Optional

import click

from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.filter_engine import build_filter_chain, apply
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line


@click.command("browse")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Number of past log lines to fetch.")
@click.option("--level", default=None, help="Minimum log level to display (e.g. info, warn, error).")
@click.option("--search", default=None, help="Highlight and filter lines containing this term.")
@click.option("--no-color", is_flag=True, default=False, help="Disable ANSI color output.")
@click.option("--follow", "-f", is_flag=True, default=False, help="Follow log output (like tail -f).")
def browse_command(
    container: str,
    tail: int,
    level: Optional[str],
    search: Optional[str],
    no_color: bool,
    follow: bool,
) -> None:
    """Stream highlighted logs from CONTAINER to stdout."""
    use_color = not no_color

    try:
        client = DockerLogClient()
    except DockerClientError as exc:
        click.echo(f"[error] {exc}", err=True)
        sys.exit(1)

    filters = build_filter_chain(level=level, search=search)

    try:
        for raw_line in client.stream_logs(container, tail=tail, follow=follow):
            entry = parse_line(raw_line)
            if entry is None:
                continue
            filtered = apply([entry], filters)
            if not filtered:
                continue
            click.echo(format_entry(entry, search_term=search, use_color=use_color))
    except DockerClientError as exc:
        click.echo(f"[error] {exc}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
