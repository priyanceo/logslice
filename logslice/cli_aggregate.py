"""CLI command: aggregate log entries into time windows."""
from __future__ import annotations

import click

from logslice.aggregator import Aggregator, AggregatorError
from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.filter_engine import build_filter_chain, apply
from logslice.log_parser import parse_lines


@click.command("aggregate")
@click.argument("container")
@click.option("--window", default=60, show_default=True, help="Window size in seconds.")
@click.option("--tail", default=200, show_default=True, help="Number of recent log lines to fetch.")
@click.option("--level", default=None, help="Filter by log level (e.g. error, info).")
@click.option("--search", default=None, help="Exact search term to filter entries.")
def aggregate_command(
    container: str,
    window: int,
    tail: int,
    level: str | None,
    search: str | None,
) -> None:
    """Aggregate log entries from CONTAINER into time windows."""
    try:
        client = DockerLogClient()
        raw_lines = list(client.stream_logs(container, tail=tail, follow=False))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc

    entries = list(parse_lines(raw_lines))
    filter_chain = build_filter_chain(level=level, search=search)
    entries = apply(filter_chain, entries)

    try:
        agg = Aggregator(window_seconds=window)
    except AggregatorError as exc:
        raise click.ClickException(str(exc)) from exc

    agg.feed(entries)
    buckets = agg.buckets()

    if not buckets:
        click.echo("No log entries matched.")
        return

    click.echo(f"Aggregated {len(entries)} entries into {len(buckets)} window(s) ({window}s each):")
    for bucket in buckets:
        click.echo(f"  {bucket.summary()}")
