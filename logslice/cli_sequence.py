"""CLI command: sequence — reorder live container logs by timestamp."""
from __future__ import annotations

import click

from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.log_parser import parse_line
from logslice.sequencer import Sequencer, SequencerError
from logslice.highlighter import format_entry
from logslice.filter_engine import build_filter_chain, apply


@click.command("sequence")
@click.argument("container")
@click.option("--buffer", default=50, show_default=True,
              help="Reorder buffer size (number of entries).")
@click.option("--level", default=None,
              help="Keep only entries at this log level.")
@click.option("--search", default=None,
              help="Fuzzy-search term to filter messages.")
@click.option("--tail", default=200, show_default=True,
              help="Number of recent log lines to fetch.")
def sequence_command(
    container: str,
    buffer: int,
    level: str | None,
    search: str | None,
    tail: int,
) -> None:
    """Stream logs from CONTAINER and emit them ordered by timestamp."""
    try:
        sequencer = Sequencer(buffer_size=buffer)
    except SequencerError as exc:
        raise click.ClickException(str(exc)) from exc

    filters = build_filter_chain(level=level, search=search)

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if not apply(filters, entry):
                continue
            for ordered in sequencer.push(entry):
                click.echo(format_entry(ordered))

        for ordered in sequencer.flush():
            click.echo(format_entry(ordered))

    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
