import click
import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from src import google_drive, google_sheets, health_connect, strava

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
        hc_stats = hc.daily_stats()[["weight_lbs", "distance_miles", "distance_miles_7d_sum"]]

    client = strava.get_client()
    strava_stats = strava.daily_runs(client, limit=strava_limit)

    combined = pd.merge(hc_stats, strava_stats, left_index=True, right_index=True, how="outer", suffixes=("_hc", "_strava")).sort_index()

    recent = combined.tail(days)
    click.echo(recent.to_string(float_format="%.1f"))


@cli.command("download-health-connect")
@click.option("--remote-healthconnect-filename", default="Health Connect.zip", show_default=True, help="Name of file in Google Drive")
@click.option("--local-healthconnect-path", default="data/Health Connect.zip", show_default=True, help="Local destination path")
@click.option("--credentials", default="google_service_account.json", show_default=True, help="Path to service account credentials file")
def download_health_connect(remote_healthconnect_filename: str, local_healthconnect_path: str, credentials: str):
    """Download Health Connect zip file from Google Drive."""
    refresh_health_connect_file(credentials, remote_healthconnect_filename, local_healthconnect_path)


def refresh_health_connect_file(
    credentials_path: str = "google_service_account.json", remote_filename="Health Connect.zip", local_path="data/Health Connect.zip"
) -> str:
    service = google_drive.get_drive_service(credentials_path)

    file_id = google_drive.find_file_by_name(service, remote_filename)

    if not file_id:
        logger.error(f"Error: File '{remote_filename}' not found in Google Drive")
        raise click.Abort()

    logger.debug(f"Found file (ID: {file_id}), downloading to {local_path}...")
    google_drive.download_file(service, file_id, local_path)

    return local_path


@cli.command("run")
@click.option("--remote-healthconnect-filename", default="Health Connect.zip", show_default=True, help="Name of file in Google Drive")
@click.option("--local-healthconnect-path", default="data/Health Connect.zip", show_default=True, help="Local destination path")
@click.option("--sheet-name", default="Automated training log", show_default=True, help="Name of Google Sheet")
@click.option("--tab-name", default="Sheet1", show_default=True, help="Name of tab within the sheet")
@click.option("--strava-limit", default=100, show_default=True, help="Number of Strava activities to fetch")
@click.option("--credentials", default="google_service_account.json", show_default=True, help="Path to service account credentials file")
def run_pipeline(
    remote_healthconnect_filename: str, local_healthconnect_path: str, credentials: str, sheet_name: str, tab_name: str, strava_limit: int
):
    """Download Health Connect data and update the Google Sheet."""
    healthconnect_path = refresh_health_connect_file(credentials, remote_healthconnect_filename, local_healthconnect_path)

    combined = load_combined_stats(healthconnect_path, strava_limit)
    sheets_service = google_sheets.get_sheets_service()
    drive_service = google_drive.get_drive_service(credentials)

    logger.debug(f"Finding spreadsheet '{sheet_name}'...")
    spreadsheet_id = google_drive.find_file_by_name(drive_service, sheet_name, google_drive.FileTypes.SHEET)

    if not spreadsheet_id:
        logger.error(f"Error: Spreadsheet '{sheet_name}' not found")
        raise click.Abort()

    logger.debug(f"Found spreadsheet (ID: {spreadsheet_id})")
    logger.debug(f"Writing {len(combined)} rows to '{tab_name}'...")
    google_sheets.write_dataframe(sheets_service, spreadsheet_id, tab_name, combined)
    click.echo("✓ Sheet updated successfully")


def load_combined_stats(health_connect_zip: str, strava_limit: int) -> pd.DataFrame:
    with health_connect.HealthConnect(health_connect_zip) as hc:
        hc_stats = hc.daily_stats()[["weight_lbs", "distance_miles", "distance_miles_7d_sum"]]

    client = strava.get_client()
    strava_stats = strava.daily_runs(client, limit=strava_limit)

    combined = pd.merge(
        hc_stats,
        strava_stats,
        left_index=True,
        right_index=True,
        how="outer",
        suffixes=("_hc", "_strava"),
    ).sort_index()

    return combined[combined.index >= pd.to_datetime("2025-01-01").date()]


if __name__ == "__main__":
    cli()
