"""CLI command: enrich log entries with derived fields."""

from __future__ import annotations

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.enricher import EnrichRule, Enricher
from logslice.filter_engine import build_filter_chain
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line


@click.command("enrich")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Number of log lines to fetch.")
@click.option("--level", default=None, help="Filter by log level.")
@click.option("--search", default=None, help="Exact-match search term.")
@click.option("--add-host/--no-add-host", default=True, show_default=True,
              help="Attach container name as 'host' field.")
@click.option("--add-index/--no-add-index", default=False, show_default=True,
              help="Attach sequential index as 'index' field.")
def enrich_command(
    container: str,
    tail: int,
    level: str | None,
    search: str | None,
    add_host: bool,
    add_index: bool,
) -> None:
    """Stream logs from CONTAINER and enrich each entry with derived fields."""
    try:
        client = DockerLogClient()
        enricher = Enricher()

        if add_host:
            enricher.add_rule(EnrichRule(key="host", derive=lambda e: container))

        if add_index:
            counter = {"n": 0}

            def _index(e):  # noqa: ANN001
                counter["n"] += 1
                return counter["n"]

            enricher.add_rule(EnrichRule(key="index", derive=_index))

        filters = build_filter_chain(level=level, search=search)

        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if entry is None:
                continue
            if not all(f(entry) for f in filters):
                continue
            enricher.enrich(entry)
            click.echo(format_entry(entry))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
