"""CLI command: split container logs into named buckets and display counts."""
from __future__ import annotations

import sys
from collections import defaultdict
from typing import List

import click

from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.log_parser import parse_line
from logslice.splitter import SplitRule, Splitter, SplitterError


@click.command("split")
@click.argument("container")
@click.option("--tail", default=100, show_default=True, help="Number of log lines to fetch.")
@click.option(
    "--level",
    "levels",
    multiple=True,
    help="Add a bucket rule matching a specific log level, e.g. --level error.",
)
@click.option(
    "--keyword",
    "keywords",
    multiple=True,
    help="Add a bucket rule matching a keyword in the message, e.g. --keyword timeout.",
)
@click.option("--catch-all", default="default", show_default=True, help="Name for unmatched entries.")
def split_command(
    container: str,
    tail: int,
    levels: List[str],
    keywords: List[str],
    catch_all: str,
) -> None:
    """Split logs from CONTAINER into named buckets and print a summary."""
    splitter = Splitter(catch_all=catch_all)

    for lvl in levels:
        lvl_lower = lvl.lower()
        splitter.add_rule(
            SplitRule(
                name=lvl_lower,
                match=lambda e, _l=lvl_lower: (e.level or "").lower() == _l,
            )
        )

    for kw in keywords:
        kw_lower = kw.lower()
        splitter.add_rule(
            SplitRule(
                name=kw_lower,
                match=lambda e, _k=kw_lower: _k in e.message.lower(),
            )
        )

    try:
        client = DockerLogClient()
        raw_lines = list(client.stream_logs(container, tail=tail, follow=False))
    except DockerClientError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    entries = [parse_line(line) for line in raw_lines if line.strip()]
    buckets = splitter.split(entries)

    click.echo(f"Split results for container '{container}':")
    for bucket_name, bucket_entries in sorted(buckets.items()):
        click.echo(f"  [{bucket_name}] {len(bucket_entries)} entries")
        for entry in bucket_entries:
            click.echo(f"    {entry}")
