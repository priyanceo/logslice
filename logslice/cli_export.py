"""CLI helper for the export sub-command of logslice."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from logslice.docker_client import DockerLogClient
from logslice.exporter import ExportFormat, export_entries
from logslice.filter_engine import apply, build_filter_chain
from logslice.log_parser import parse_lines


@click.command("export")
@click.argument("container")
@click.option(
    "--format",
    "fmt",
    type=click.Choice([f.value for f in ExportFormat], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format for exported logs.",
)
@click.option("--level", default=None, help="Filter by log level (e.g. ERROR).")
@click.option("--search", default=None, help="Exact keyword to search in log messages.")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Write output to a file instead of stdout.",
)
@click.option("--tail", default=200, show_default=True, help="Number of recent log lines to fetch.")
def export_command(
    container: str,
    fmt: str,
    level: Optional[str],
    search: Optional[str],
    output: Optional[str],
    tail: int,
) -> None:
    """Export logs from CONTAINER to the chosen format."""
    client = DockerLogClient()
    try:
        raw_lines = client.fetch_logs(container, tail=tail)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error fetching logs: {exc}", err=True)
        sys.exit(1)

    entries = list(parse_lines(raw_lines))

    filters = build_filter_chain(level=level, search=search)
    filtered = list(apply(entries, filters))

    result = export_entries(filtered, fmt)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Exported {len(filtered)} entries to {output}")
    else:
        click.echo(result)
