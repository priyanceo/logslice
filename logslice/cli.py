"""Unified CLI entry-point for logslice."""
from __future__ import annotations

import click

from logslice.cli_browse import browse_command
from logslice.cli_export import export_command
from logslice.cli_tui import browse_command as tui_command
from logslice.cli_stats import stats_command
from logslice.cli_alert import alert_command
from logslice.cli_replay import replay_command
from logslice.cli_sample import sample_command
from logslice.cli_dedup import dedup_command
from logslice.cli_aggregate import aggregate_command
from logslice.cli_transform import transform_command


@click.group()
@click.version_option(package_name="logslice")
def cli() -> None:
    """logslice — filter, tail, and export structured logs from Docker containers."""


cli.add_command(browse_command, name="browse")
cli.add_command(tui_command, name="tui")
cli.add_command(export_command, name="export")
cli.add_command(stats_command, name="stats")
cli.add_command(alert_command, name="alert")
cli.add_command(replay_command, name="replay")
cli.add_command(sample_command, name="sample")
cli.add_command(dedup_command, name="dedup")
cli.add_command(aggregate_command, name="aggregate")
cli.add_command(transform_command, name="transform")


if __name__ == "__main__":  # pragma: no cover
    cli()
