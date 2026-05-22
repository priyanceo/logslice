"""CLI command to launch the interactive TUI log browser."""

import sys
import click
from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.log_parser import parse_lines
from logslice.tui import launch_tui


@click.command("browse")
@click.argument("container")
@click.option("--tail", default=200, show_default=True, help="Number of log lines to load.")
@click.option("--level", default=None, help="Pre-filter by log level (e.g. error, info).")
def browse_command(container: str, tail: int, level: str) -> None:
    """Interactively browse logs from CONTAINER with fuzzy search."""
    try:
        client = DockerLogClient()
        raw_lines = client.fetch_logs(container, tail=tail)
    except DockerClientError as exc:
        click.echo(f"Docker error: {exc}", err=True)
        sys.exit(1)

    entries = parse_lines(raw_lines)

    if level:
        entries = [e for e in entries if (e.level or "").lower() == level.lower()]

    if not entries:
        click.echo("No log entries found.", err=True)
        sys.exit(0)

    selected = launch_tui(entries)

    if selected:
        click.echo(str(selected))
