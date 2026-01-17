import click
import pandas as pd
from dotenv import load_dotenv

from src import health_connect, strava

# Load environment variables from .env file
load_dotenv()


@click.group()
def cli():
    """Fitness data ETL pipeline for marathon training tracking."""
    pass


@cli.group("health-connect")
def health_connect_group():
    pass


@health_connect_group.command("show-tables")
@click.argument("zip_path", type=click.Path(exists=True))
def show_tables(zip_path: str):
    """Show all tables in the Health Connect database with row counts."""
    with health_connect.HealthConnect(zip_path) as hc:
        hc.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = hc.cursor.fetchall()

        for table_name in tables:
            table_name = table_name[0]
            hc.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            num_rows = hc.cursor.fetchone()[0]
            click.echo(f"  {table_name:<40} {num_rows:>8} rows")


@health_connect_group.command("show-daily-stats")
@click.argument("zip_path", type=click.Path(exists=True))
@click.option("--days", default=14, show_default=True, help="Number of recent days to display")
def show_daily_stats(zip_path: str, days: int):
    """Show daily weight and distance statistics."""
    with health_connect.HealthConnect(zip_path) as hc:
        daily_stats = hc.daily_stats()
        recent_stats = daily_stats.tail(days)[["weight_lbs", "distance_miles", "distance_miles_7d_sum"]]
        click.echo(recent_stats.to_string(float_format="%.1f"))


@cli.group("strava")
def strava_group():
    pass


@strava_group.command("show-runs")
@click.option("--limit", default=14, show_default=True, help="Number of most recent activities to fetch")
def show_runs(limit: int):
    """Show recent run statistics from Strava."""
    client = strava.get_client()
    runs_df = strava.daily_runs(client, limit=limit)
    click.echo(runs_df.to_string(float_format="%.1f"))

@cli.command("daily-stats")
@click.argument("health_connect_zip", type=click.Path(exists=True))
@click.option("--days", default=14, show_default=True, help="Number of recent days to display")
@click.option("--strava-limit", default=30, show_default=True, help="Number of Strava activities to fetch")
def daily_stats(health_connect_zip: str, days: int, strava_limit: int):
    """Show unified daily statistics from Health Connect and Strava."""
    with health_connect.HealthConnect(health_connect_zip) as hc:
        hc_stats = hc.daily_stats()[['weight_lbs', 'distance_miles', 'distance_miles_7d_sum']]
    
    client = strava.get_client()
    strava_stats = strava.daily_runs(client, limit=strava_limit)
    
    combined = pd.merge(
        hc_stats,
        strava_stats,
        left_index=True,
        right_index=True,
        how='outer',
        suffixes=('_hc', '_strava')
    ).sort_index()
    
    recent = combined.tail(days)
    click.echo(recent.to_string(float_format='%.1f'))

if __name__ == "__main__":
    cli()
