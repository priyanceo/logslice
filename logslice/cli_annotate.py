"""CLI command: annotate – stream logs and attach tags based on simple rules."""
from __future__ import annotations

import click

from logslice.annotator import AnnotationRule, Annotator
from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.highlighter import format_entry
from logslice.log_parser import parse_line


@click.command("annotate")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Lines to fetch from log tail.")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    metavar="TAG:PATTERN",
    help="Add TAG when message contains PATTERN (repeatable).",
)
@click.option("--level", default=None, help="Only show entries at this log level.")
def annotate_command(
    container: str,
    tail: int,
    tags: tuple,
    level: str | None,
) -> None:
    """Stream logs from CONTAINER and annotate matching lines with custom tags."""
    annotator = Annotator()
    for spec in tags:
        if ":" not in spec:
            raise click.BadParameter(f"Expected TAG:PATTERN, got '{spec}'", param_hint="--tag")
        tag, _, pattern = spec.partition(":")
        lower_pattern = pattern.lower()
        annotator.add_rule(
            AnnotationRule(
                tag=tag.strip(),
                match=lambda e, p=lower_pattern: p in e.message.lower(),
                value=pattern,
            )
        )

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail):
            entry = parse_line(raw)
            if level and (entry.level or "").lower() != level.lower():
                continue
            annotated = annotator.annotate(entry)
            line = format_entry(annotated)
            if annotated.extra:
                tags_str = " ".join(f"[{k}={v}]" for k, v in annotated.extra.items())
                line = f"{line} {tags_str}"
            click.echo(line)
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
