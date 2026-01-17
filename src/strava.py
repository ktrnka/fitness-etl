import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd
from stravalib import Client
from stravalib.protocol import AccessInfo

credential_path = "strava_credentials.json"

METERS_PER_MILE = 1609.34
SECONDS_PER_MINUTE = 60


def save_credentials(access_token, refresh_token, expires_at):
    with open(credential_path, "w") as f:
        json.dump({"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at}, f)


def load_credentials() -> AccessInfo:
    with open(credential_path, "r") as f:
        credentials = json.load(f)
    return AccessInfo(**credentials)


def get_authorization_url():
    client = Client()
    url = client.authorization_url(
        client_id=int(os.environ["STRAVA_CLIENT_ID"]),
        redirect_uri="http://localhost/authorization",
    )
    return url


def get_client() -> Client:
    os.environ["SILENCE_TOKEN_WARNINGS"] = "true"

    access_info = load_credentials()
    client = Client(access_token=access_info["access_token"])

    if access_info["expires_at"] < time.time():
        print("Refreshing access token")
        access_info = client.refresh_access_token(
            client_id=int(os.environ["STRAVA_CLIENT_ID"]),
            client_secret=os.environ["STRAVA_CLIENT_SECRET"],
            refresh_token=access_info["refresh_token"],
        )
        save_credentials(**access_info)
        client = Client(access_token=access_info["access_token"])

    athlete = client.get_athlete()
    print(f"Signed in as {athlete.firstname} {athlete.lastname}")

    return client


def daily_runs(client, limit: int = 14) -> pd.DataFrame:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    activities = client.get_activities(before=tomorrow, limit=limit)

    runs_data = []
    for activity in activities:
        if activity.type == "Run":
            distance_miles = float(activity.distance) / METERS_PER_MILE
            moving_time_minutes = float(activity.moving_time) / SECONDS_PER_MINUTE
            minutes_per_mile = moving_time_minutes / distance_miles if distance_miles > 0 else 0

            runs_data.append(
                {
                    "date": activity.start_date_local.date(),
                    "distance_miles": distance_miles,
                    "moving_time_minutes": moving_time_minutes,
                    "minutes_per_mile": minutes_per_mile,
                }
            )

    if not runs_data:
        return pd.DataFrame()

    df = pd.DataFrame(runs_data)
    return df.set_index("date").sort_index()
