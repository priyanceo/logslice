"""CLI command: transform — apply field redaction/replacement rules to streamed logs."""
from __future__ import annotations

import sys
import click

from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.log_parser import parse_line
from logslice.transformer import Transformer, TransformRule
from logslice.highlighter import format_entry


@click.command("transform")
@click.argument("container")
@click.option(
    "--redact",
    multiple=True,
    metavar="PATTERN",
    help="Regex pattern to redact from message (replace with [REDACTED]).",
)
@click.option(
    "--replace",
    "replacements",
    multiple=True,
    metavar="FIELD:PATTERN:REPL",
    help="Field-level replacement in FIELD:PATTERN:REPLACEMENT format.",
)
@click.option("--tail", default=100, show_default=True, help="Number of log lines to fetch.")
@click.option("--no-color", is_flag=True, default=False, help="Disable ANSI color output.")
def transform_command(
    container: str,
    redact: tuple,
    replacements: tuple,
    tail: int,
    no_color: bool,
) -> None:
    """Stream logs from CONTAINER with field transformations applied."""
    transformer = Transformer()

    for pat in redact:
        transformer.add_rule(TransformRule(field="message", pattern=pat, replacement="[REDACTED]"))

    for spec in replacements:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            click.echo(f"Invalid --replace spec '{spec}' (expected FIELD:PATTERN:REPL)", err=True)
            sys.exit(1)
        fld, pat, repl = parts
        transformer.add_rule(TransformRule(field=fld, pattern=pat, replacement=repl))

    try:
        client = DockerLogClient()
        for raw_line in client.stream_logs(container, tail=tail):
            entry = parse_line(raw_line)
            entry = transformer.transform(entry)
            click.echo(format_entry(entry, colorize=not no_color))
    except DockerClientError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
