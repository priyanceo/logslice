"""CLI command: classify log entries from a Docker container."""
from __future__ import annotations

import click

from logslice.classifier import Classifier, ClassifierError, ClassifyRule
from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.filter_engine import build_filter_chain, apply as apply_filters
from logslice.log_parser import parse_line


@click.command("classify")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Number of log lines to fetch.")
@click.option("--level", default=None, help="Only show entries at this log level.")
@click.option("--keyword", "-k", multiple=True, help="Keyword rules: 'category:pattern' e.g. error:exception.")
@click.option("--default-category", default="uncategorized", show_default=True)
def classify_command(
    container: str,
    tail: int,
    level: str | None,
    keyword: tuple[str, ...],
    default_category: str,
) -> None:
    """Classify log entries from CONTAINER and print each line with its category."""
    classifier = Classifier(default_category=default_category)

    for spec in keyword:
        if ":" not in spec:
            raise click.BadParameter(f"Keyword rule must be 'category:pattern', got: {spec!r}")
        cat, pattern = spec.split(":", 1)
        cat = cat.strip()
        pat = pattern.strip().lower()
        classifier.add_rule(
            ClassifyRule(
                name=f"{cat}:{pat}",
                match=lambda e, p=pat: p in e.message.lower(),
                category=cat,
            )
        )

    filters = build_filter_chain(level=level)

    try:
        client = DockerLogClient()
        raw_lines = list(client.stream_logs(container, tail=tail))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc

    entries = [parse_line(line) for line in raw_lines if line.strip()]
    entries = apply_filters(entries, filters)

    for entry in entries:
        category = classifier.classify(entry)
        click.echo(f"[{category}] {entry}")
