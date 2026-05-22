"""CLI command for displaying log statistics from a Docker container."""

import click
from logslice.docker_client import DockerLogClient, DockerClientError
from logslice.log_parser import parse_lines
from logslice.stats import compute_stats


@click.command("stats")
@click.argument("container")
@click.option("--tail", default=500, show_default=True, help="Number of log lines to read.")
@click.option("--level", is_flag=True, default=False, help="Show breakdown by log level.")
@click.option("--service", is_flag=True, default=False, help="Show breakdown by service.")
@click.option("--top", default=5, show_default=True, help="Top N entries for breakdowns.")
def stats_command(container: str, tail: int, level: bool, service: bool, top: int) -> None:
    """Show statistics for logs from CONTAINER."""
    try:
        client = DockerLogClient()
        raw_lines = list(client.stream_logs(container, tail=tail))
    except DockerClientError as exc:
        raise click.ClickException(str(exc)) from exc

    entries = list(parse_lines(raw_lines))
    if not entries:
        click.echo("No log entries found.")
        return

    stats = compute_stats(entries)
    summary = stats.summary()

    click.echo(f"Container : {container}")
    click.echo(f"Total logs: {summary['total']}")
    click.echo(f"Time range: {summary['first_timestamp']} -> {summary['last_timestamp']}")

    if level:
        click.echo("\nBy level:")
        by_level = sorted(summary["by_level"].items(), key=lambda x: x[1], reverse=True)
        for lvl, count in by_level[:top]:
            click.echo(f"  {lvl:<12} {count}")

    if service:
        click.echo("\nBy service:")
        by_service = sorted(summary["by_service"].items(), key=lambda x: x[1], reverse=True)
        for svc, count in by_service[:top]:
            click.echo(f"  {svc:<20} {count}")
