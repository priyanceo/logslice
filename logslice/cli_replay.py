"""CLI command: replay a saved log file through logslice."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from logslice.filter_engine import build_filter_chain
from logslice.highlighter import format_entry
from logslice.replay import ReplayError, replay


@click.command("replay")
@click.argument("file", type=click.Path(exists=False))
@click.option("--level", default=None, help="Filter by log level (e.g. ERROR).")
@click.option("--search", default=None, help="Fuzzy search term.")
@click.option("--exact", default=None, help="Exact substring match.")
@click.option("--no-color", is_flag=True, default=False, help="Disable ANSI colours.")
def replay_command(
    file: str,
    level: str | None,
    search: str | None,
    exact: str | None,
    no_color: bool,
) -> None:
    """Replay a saved log FILE through the logslice pipeline."""
    path = Path(file)
    chain = build_filter_chain(level=level, search=search, exact=exact)

    try:
        count = 0
        for entry in replay(path, filters=chain):
            if no_color:
                click.echo(str(entry))
            else:
                click.echo(format_entry(entry, highlight_term=search))
            count += 1
        click.echo(f"\n{count} line(s) matched.", err=True)
    except ReplayError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
