"""CLI command: stream logs and fire alerts based on level/keyword thresholds."""
from __future__ import annotations

import click

from logslice.alerter import AlertEngine, AlertRule
from logslice.docker_client import DockerClientError, DockerLogClient
from logslice.highlighter import format_entry, highlight_level
from logslice.log_parser import LogEntry, parse_line


def _default_callback(rule: "AlertRule", entry: "LogEntry") -> None:
    click.echo(
        click.style(
            f"[ALERT] Rule '{rule.name}' triggered — {entry.level}: {entry.message}",
            fg="red",
            bold=True,
        )
    )


@click.command("alert")
@click.argument("container")
@click.option("--level", default="ERROR", show_default=True, help="Log level to watch.")
@click.option("--keyword", default=None, help="Optional keyword filter.")
@click.option("--threshold", default=1, show_default=True, type=int, help="Hit count before alert fires.")
@click.option("--window", default=60, show_default=True, type=int, help="Rolling window in seconds (0 = unlimited).")
@click.option("--rule-name", default="cli-alert", show_default=True, help="Name for the alert rule.")
def alert_command(
    container: str,
    level: str,
    keyword: str | None,
    threshold: int,
    window: int,
    rule_name: str,
) -> None:
    """Stream logs from CONTAINER and alert when a rule threshold is reached."""
    rule = AlertRule(
        level=level.upper(),
        keyword=keyword,
        threshold=threshold,
        window=window,
        name=rule_name,
    )

    engine = AlertEngine()
    engine.add_rule(rule)
    engine.on_alert(_default_callback)

    try:
        client = DockerLogClient()
        click.echo(f"Watching container '{container}' for level={level}, threshold={threshold} ...")
        for raw_line in client.stream_logs(container):
            entry = parse_line(raw_line)
            click.echo(format_entry(entry, term=keyword))
            engine.process(entry)
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc
