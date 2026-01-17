import json
import os
import time

from stravalib import Client
from stravalib.protocol import AccessInfo

credential_path = "/content/drive/MyDrive/Physical Training/.strava_credentials.json"


def save_credentials(access_token, refresh_token, expires_at):
    with open(credential_path, "w") as f:
        json.dump({"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at}, f)


def load_credentials() -> AccessInfo:
    with open(credential_path, "r") as f:
        credentials = json.load(f)
    return AccessInfo(**credentials)


def get_authorization_url():
    """If you need to re-authenticate, run this to get the URL to visit."""
    client = Client()
    url = client.authorization_url(
        client_id=int(os.environ["STRAVA_CLIENT_ID"]),
        redirect_uri="http://localhost/authorization",
    )
    return url


# access_info = client.exchange_code_for_token(
#     client_id=int(os.environ['STRAVA_CLIENT_ID']), client_secret=os.environ['STRAVA_CLIENT_SECRET'], code="XXX"
# )
# save_credentials(**access_info)


def get_client() -> Client:
    os.environ["SILENCE_TOKEN_WARNINGS"] = "true"

    access_info = load_credentials()
    client = Client(access_token=access_info["access_token"])

    if access_info["expires_at"] < time.time():
        # Get new access info
        print("Refreshing access token")
        access_info = client.refresh_access_token(
            client_id=int(os.environ["STRAVA_CLIENT_ID"]),
            client_secret=os.environ["STRAVA_CLIENT_SECRET"],
            refresh_token=access_info["refresh_token"],
        )
        assert access_info

        save_credentials(**access_info)

        client = Client(access_token=access_info["access_token"])

    # For debugging
    athlete = client.get_athlete()
    print(f"Signed in as {athlete.firstname} {athlete.lastname}")

    return client

# METERS_PER_MILE = 1609.34

def iterate_runs(client):
    # TODO: Configuration of the before / limit
    activities = client.get_activities(before="2026-02-01", limit=10)
    for activity in activities:
        if activity.type == "Run":
            yield activity
            # distance_miles = activity.distance / METERS_PER_MILE
            # moving_time_minutes = activity.moving_time / 60
            # minutes_per_mile = moving_time_minutes / distance_miles
            # start_dt = activity.start_date_local

            # print(f"{start_dt.date()} | {distance_miles:.1f} mi @ {minutes_per_mile:.1f} min/mile | {activity.total_elevation_gain} ft elevation gain")