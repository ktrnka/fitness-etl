import click
import pandas as pd

from src import health_connect


@click.group()
def cli():
    """Fitness data ETL pipeline for marathon training tracking."""
    pass


@cli.group("health-connect")
def health_connect_group():
    """Commands for working with Health Connect data."""
    pass


@health_connect_group.command("show-tables")
@click.argument("zip_path", type=click.Path(exists=True))
def show_tables(zip_path: str):
    """Show all tables in the Health Connect database with row counts.
    
    Example:
        fitness health-connect show-tables "data/Health Connect.zip"
    """
    click.echo(f"Loading Health Connect data from: {zip_path}")
    click.echo()
    
    try:
        with health_connect.HealthConnect(zip_path) as hc:
            click.echo("Tables in the database:")
            click.echo("-" * 50)
            hc.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = hc.cursor.fetchall()
            
            for table_name in tables:
                table_name = table_name[0]
                hc.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                num_rows = hc.cursor.fetchone()[0]
                click.echo(f"  {table_name:<40} {num_rows:>8} rows")
            
            click.echo()
            click.echo("✅ Database loaded successfully!")
            
    except Exception as e:
        click.echo(f"❌ Error loading Health Connect data: {e}", err=True)
        raise click.Abort()


@health_connect_group.command("show-daily-stats")
@click.argument("zip_path", type=click.Path(exists=True))
@click.option("--days", default=14, help="Number of recent days to display (default: 14)")
def show_daily_stats(zip_path: str, days: int):
    """Show daily statistics including weight and distance data.
    
    Example:
        fitness health-connect show-daily-stats "data/Health Connect.zip"
        fitness health-connect show-daily-stats "data/Health Connect.zip" --days 30
    """
    try:
        with health_connect.HealthConnect(zip_path) as hc:
            daily_stats = hc.daily_stats()
            
            if daily_stats.empty:
                click.echo("No data found in the Health Connect database.")
                return
            
            recent_stats = daily_stats.tail(days)[['weight_lbs', 'distance_miles', 'distance_miles_7d_sum']]
            click.echo(recent_stats.to_string(float_format='%.1f'))
            
    except Exception as e:
        click.echo(f"❌ Error loading Health Connect data: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()

