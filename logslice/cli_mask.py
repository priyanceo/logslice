"""CLI command: mask sensitive fields in streamed container logs."""
from __future__ import annotations

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.filter_engine import build_filter_chain, apply
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line
from logslice.masker import MaskRule, Masker, MaskerError


@click.command("mask")
@click.argument("container")
@click.option("--field", "fields", multiple=True, default=["message"],
              show_default=True, help="Fields to mask (repeatable).")
@click.option("--mask-with", default="***", show_default=True,
              help="Replacement string for masked values.")
@click.option("--level", default=None, help="Only show entries at this log level.")
@click.option("--search", default=None, help="Exact-match filter on message.")
@click.option("--tail", default=100, show_default=True,
              help="Number of recent lines to fetch.")
def mask_command(
    container: str,
    fields: tuple,
    mask_with: str,
    level: str | None,
    search: str | None,
    tail: int,
) -> None:
    """Stream logs from CONTAINER with sensitive fields masked."""
    try:
        masker = Masker()
        masker.add_rule(
            MaskRule(name="cli-mask", fields=list(fields), mask_with=mask_with)
        )
    except MaskerError as exc:
        raise click.ClickException(str(exc)) from exc

    chain = build_filter_chain(level=level, search=search)

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if not apply(chain, entry):
                continue
            masked = masker.apply(entry)
            click.echo(format_entry(masked))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
