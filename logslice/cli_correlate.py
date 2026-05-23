"""CLI command: correlate log entries by trace ID or time window."""
from __future__ import annotations

import json
import sys

import click

from logslice.correlator import Correlator, CorrelatorConfig, CorrelatorError
from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.log_parser import parse_line


@click.command("correlate")
@click.argument("container")
@click.option("--field", default="trace_id", show_default=True,
              help="Extra JSON field to group entries by.")
@click.option("--window", default=5.0, show_default=True, type=float,
              help="Fallback time-window size in seconds.")
@click.option("--min-size", default=2, show_default=True, type=int,
              help="Minimum entries per group to display.")
@click.option("--tail", default=200, show_default=True, type=int,
              help="Number of recent log lines to fetch.")
@click.option("--json-out", is_flag=True, default=False,
              help="Output groups as JSON instead of plain text.")
def correlate_command(
    container: str,
    field: str,
    window: float,
    min_size: int,
    tail: int,
    json_out: bool,
) -> None:
    """Group log entries from CONTAINER by trace ID or time proximity."""
    try:
        cfg = CorrelatorConfig(field=field, window_seconds=window, min_group_size=min_size)
    except CorrelatorError as exc:
        click.echo(f"Configuration error: {exc}", err=True)
        sys.exit(1)

    correlator = Correlator(config=cfg)

    try:
        client = DockerLogClient()
        for raw in client.stream_logs(container, tail=tail, follow=False):
            entry = parse_line(raw)
            correlator.feed(entry)
    except DockerClientError as exc:
        click.echo(f"Docker error: {exc}", err=True)
        sys.exit(1)

    groups = correlator.groups()
    if not groups:
        click.echo("No groups found matching the criteria.")
        return

    if json_out:
        click.echo(json.dumps([g.summary() for g in groups], indent=2))
    else:
        for g in groups:
            s = g.summary()
            click.echo(
                f"[{s['key']}]  entries={s['count']}  "
                f"levels={s['levels']}  services={s['services']}"
            )
