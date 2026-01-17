# fitness-etl

ETL pipeline for consolidating fitness data from multiple sources to track marathon training progress.

## Overview

Training for a marathon in Fall 2026. This pipeline consolidates fragmented fitness data from Google Health Connect and Strava into a unified Google Sheet for consistent tracking. The pipeline runs daily via GitHub Actions to provide an up-to-date view of training metrics.

### Data Sources

- **Weight**: Manually tracked, synced via Health Connect
- **Steps/Distance**: Auto-tracked, synced via Health Connect  
- **Running Activities**: Tracked in Strava, accessed via API

### The Goal

Maintain a single, consolidated view of all training metrics to track progress toward marathon readiness. The pipeline handles incremental updates, only fetching new data since the last run.

## Architecture

### Data Flow

1. **Health Connect** → Daily SQLite dump to Google Drive (zip file)
2. **Strava API** → Incremental fetch of new activities  
3. **Google Sheets** → Unified output with all training metrics

### Status

✅ **Working**
- Health Connect data extraction and daily aggregation
- Strava API integration with token refresh
- CLI for local testing

⏳ **Next Steps**
- Google Drive integration (read/write)
- Google Sheets output writer
- GitHub Actions automation

## Setup

### Prerequisites

- Python 3.13
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
git clone https://github.com/ktrnka/fitness-etl.git
cd fitness-etl
uv sync
```

### Configuration

Create `.env` file:

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

Get Strava credentials at https://www.strava.com/settings/api

## Usage

### Test with Local Data

```bash
# Show database contents
uv run fitness health-connect show-tables "data/Health Connect.zip"

# View recent statistics
uv run fitness health-connect show-daily-stats "data/Health Connect.zip"
uv run fitness health-connect show-daily-stats "data/Health Connect.zip" --days 30
```

### Run Pipeline (Coming Soon)

```bash
uv run fitness run
```

## TODO

### High Priority
- [ ] Google Drive integration (read Health Connect zip, store Strava tokens)
- [ ] Google Sheets output writer
- [ ] GitHub Actions workflow for daily runs
- [ ] Incremental ETL: only fetch Strava activities since last known date
- [ ] Unit tests

### Future Enhancements
- [ ] Data visualization
- [ ] Historical backfill
- [ ] Additional data sources

## License

MIT
