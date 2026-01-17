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
- Google Drive integration (download Health Connect zip)
- Google Sheets output writer (basic overwrite mode)
- GitHub Actions authentication via Workload Identity
- CLI for local testing

⏳ **Next Steps**
- Strava token storage solution for GitHub Actions
- Incremental Google Sheets updates (preserve user columns, better headers)
- Full automated pipeline

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
# Health Connect
uv run fitness health-connect show-tables "data/Health Connect.zip"
uv run fitness health-connect show-daily-stats "data/Health Connect.zip"
uv run fitness health-connect show-daily-stats "data/Health Connect.zip" --days 30

# Strava
uv run fitness strava show-runs
uv run fitness strava show-runs --limit 30
```

### Run Pipeline (Coming Soon)

```bash
uv run fitness run
```

## Development

### Coding Standards

- **Minimal code**: Every line has a maintenance cost - each must be worth it
- **Comments/docstrings**: Only when they add value beyond names and types
- **CLI**: Let errors crash with stack traces (no try/except wrapping)
- **Options**: Use `show_default=True` for automatic default value display
- **Units**: All unit conversions in `src/units.py`

## TODO

### High Priority
- [ ] Strava token storage/refresh solution for GitHub Actions
- [ ] Incremental Google Sheets ETL (preserve user-added columns, improve headers)
- [ ] Full automated daily pipeline workflow
- [ ] Unit tests

### Future Enhancements
- [ ] Data visualization
- [ ] Historical backfill
- [ ] Additional data sources

## License

MIT
