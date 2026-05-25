"""Root CLI entry-point for logslice."""
from __future__ import annotations

import click

from logslice.cli_export import export_command
from logslice.cli_tui import browse_command as tui_command
from logslice.cli_browse import browse_command
from logslice.cli_stats import stats_command
from logslice.cli_alert import alert_command
from logslice.cli_replay import replay_command
from logslice.cli_sample import sample_command
from logslice.cli_dedup import dedup_command
from logslice.cli_aggregate import aggregate_command
from logslice.cli_transform import transform_command
from logslice.cli_correlate import correlate_command
from logslice.cli_annotate import annotate_command
from logslice.cli_rate_limit import rate_limit_command
from logslice.cli_route import route_command
from logslice.cli_split import split_command
from logslice.cli_enrich import enrich_command
from logslice.cli_mask import mask_command


@click.group()
@click.version_option()
def cli() -> None:
    """logslice — filter, tail, and export structured Docker logs."""


cli.add_command(export_command, name="export")
cli.add_command(tui_command, name="tui")
cli.add_command(browse_command, name="browse")
cli.add_command(stats_command, name="stats")
cli.add_command(alert_command, name="alert")
cli.add_command(replay_command, name="replay")
cli.add_command(sample_command, name="sample")
cli.add_command(dedup_command, name="dedup")
cli.add_command(aggregate_command, name="aggregate")
cli.add_command(transform_command, name="transform")
cli.add_command(correlate_command, name="correlate")
cli.add_command(annotate_command, name="annotate")
cli.add_command(rate_limit_command, name="rate-limit")
cli.add_command(route_command, name="route")
cli.add_command(split_command, name="split")
cli.add_command(enrich_command, name="enrich")
cli.add_command(mask_command, name="mask")
