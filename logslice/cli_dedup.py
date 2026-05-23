"""CLI command: stream container logs with duplicate suppression."""
from __future__ import annotations

import click

from logslice.deduplicator import Deduplicator, DeduplicatorConfig
from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.filter_engine import build_filter_chain
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line


@click.command("dedup")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Lines to fetch initially.")
@click.option("--level", default=None, help="Filter by log level (e.g. ERROR).")
@click.option("--search", default=None, help="Exact substring filter.")
@click.option(
    "--window", default=256, show_default=True, help="Dedup hash-window size."
)
@click.option(
    "--max-repeats",
    default=1,
    show_default=True,
    help="Allow each unique line this many times before suppressing.",
)
@click.option("--no-color", is_flag=True, default=False, help="Disable ANSI colours.")
def dedup_command(
    container: str,
    tail: int,
    level: str | None,
    search: str | None,
    window: int,
    max_repeats: int,
    no_color: bool,
) -> None:
    """Stream logs from CONTAINER with duplicate lines suppressed."""
    cfg = DeduplicatorConfig(
        window_size=window,
        max_repeats=max_repeats,
        on_suppressed=lambda e, n: click.echo(
            click.style(f"  [suppressed duplicate #{n}: {e.message!r}]", fg="yellow"),
            err=True,
        ),
    )
    dedup = Deduplicator(cfg)
    chain = build_filter_chain(level=level, search=search)

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if not chain.apply(entry):
                continue
            if not dedup.should_keep(entry):
                continue
            click.echo(format_entry(entry, colorize=not no_color))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
