"""CLI command: stream Docker logs with a per-second rate cap."""
from __future__ import annotations

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.filter_engine import build_filter_chain, apply
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line
from logslice.rate_limiter import RateLimiter, RateLimiterError


@click.command("rate-limit")
@click.argument("container")
@click.option("--max-per-second", "-r", default=10.0, show_default=True,
              type=float, help="Maximum log entries forwarded per second.")
@click.option("--level", "-l", default=None, help="Filter by log level.")
@click.option("--search", "-s", default=None, help="Fuzzy search term.")
@click.option("--tail", "-n", default=100, show_default=True,
              type=int, help="Number of recent lines to fetch.")
def rate_limit_command(
    container: str,
    max_per_second: float,
    level: str | None,
    search: str | None,
    tail: int,
) -> None:
    """Stream logs from CONTAINER, capped to MAX_PER_SECOND entries/sec."""
    try:
        limiter = RateLimiter(max_per_second=max_per_second)
    except RateLimiterError as exc:
        raise click.BadParameter(str(exc), param_hint="--max-per-second") from exc

    try:
        client = DockerLogClient()
        raw_stream = client.stream_logs(container, tail=tail)
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc

    filters = build_filter_chain(level=level, search=search)

    for raw in raw_stream:
        entry = parse_line(raw)
        if not apply(filters, entry):
            continue
        if limiter.allow():
            click.echo(format_entry(entry))
