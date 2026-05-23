"""CLI sub-command: sample — stream logs with nth/rate sampling applied."""

from __future__ import annotations

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.filter_engine import build_filter_chain, apply
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line
from logslice.sampler import Sampler, SamplerError


@click.command("sample")
@click.argument("container")
@click.option("--every-nth", default=1, show_default=True,
              help="Keep every Nth log entry.")
@click.option("--rate", default=1.0, show_default=True,
              help="Random keep probability (0.0 < rate <= 1.0).")
@click.option("--level", default=None, help="Filter by log level (e.g. ERROR).")
@click.option("--search", default=None, help="Fuzzy search term.")
@click.option("--tail", default=100, show_default=True,
              help="Number of recent lines to fetch.")
def sample_command(
    container: str,
    every_nth: int,
    rate: float,
    level: str | None,
    search: str | None,
    tail: int,
) -> None:
    """Stream logs from CONTAINER with sampling applied."""
    try:
        sampler = Sampler(every_nth=every_nth, rate=rate)
    except SamplerError as exc:
        raise click.BadParameter(str(exc)) from exc

    chain = build_filter_chain(level=level, search=search)

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if not apply(chain, entry):
                continue
            if not sampler.should_keep(entry):
                continue
            click.echo(format_entry(entry, highlight=search))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
