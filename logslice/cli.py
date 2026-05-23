"""Root CLI entry-point for logslice."""
from __future__ import annotations

import click

from logslice.cli_alert import alert_command
from logslice.cli_aggregate import aggregate_command
from logslice.cli_annotate import annotate_command
from logslice.cli_browse import browse_command
from logslice.cli_correlate import correlate_command
from logslice.cli_dedup import dedup_command
from logslice.cli_export import export_command
from logslice.cli_rate_limit import rate_limit_command
from logslice.cli_replay import replay_command
from logslice.cli_route import route_command
from logslice.cli_sample import sample_command
from logslice.cli_split import split_command
from logslice.cli_stats import stats_command
from logslice.cli_transform import transform_command
from logslice.cli_tui import browse_command as tui_command


@click.group()
@click.version_option()
def cli() -> None:
    """logslice — filter, tail, and export structured Docker logs."""


cli.add_command(alert_command, "alert")
cli.add_command(aggregate_command, "aggregate")
cli.add_command(annotate_command, "annotate")
cli.add_command(browse_command, "browse")
cli.add_command(correlate_command, "correlate")
cli.add_command(dedup_command, "dedup")
cli.add_command(export_command, "export")
cli.add_command(rate_limit_command, "rate-limit")
cli.add_command(replay_command, "replay")
cli.add_command(route_command, "route")
cli.add_command(sample_command, "sample")
cli.add_command(split_command, "split")
cli.add_command(stats_command, "stats")
cli.add_command(transform_command, "transform")
cli.add_command(tui_command, "tui")
