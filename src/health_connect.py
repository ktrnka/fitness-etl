import os
import sqlite3
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile

import pandas as pd

# Conversion factors
GRAMS_TO_POUNDS = 0.00220462
METERS_TO_MILES = 0.000621371


class HealthConnect:
    """Extract the Health Connect db in a secure-ish manner and provide access to the DB in self.conn and self.cursor"""

    def __init__(self, zip_file_path: str):
        self.zip_file_path = zip_file_path
        self.db_file = "health_connect_export.db"

        self.temp_dir_path = None
        self.conn = None

    def __enter__(self):
        self.temp_dir_path = mkdtemp()

        with ZipFile(self.zip_file_path, "r") as zip_ref:
            zip_ref.extract(self.db_file, self.temp_dir_path)

        extracted_db_path = os.path.join(self.temp_dir_path, self.db_file)

        # Connect to the SQLite database
        self.conn = sqlite3.connect(extracted_db_path)
        self.cursor = self.conn.cursor()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
        if self.temp_dir_path:
            rmtree(self.temp_dir_path)

    def weight_table(
        self,
    ) -> pd.DataFrame:
        date_args = dict(unit="ms", origin="unix")
        return pd.read_sql(
            "SELECT * FROM weight_record_table",
            self.conn,
            parse_dates={"last_modified_time": date_args, "time": date_args, "local_date_time": date_args},
            index_col="row_id",
        )

        # TODO:
        # local_date_time has the time zone offset ok but not daylight savings time

    def daily_weight(
        self,
    ) -> pd.Series:
        weight_df = self.weight_table()

        weight_df["local_date"] = weight_df["local_date_time"].dt.date

        return weight_df.groupby("local_date")["weight"].mean().sort_index()

    def distance_table(
        self,
    ) -> pd.DataFrame:
        date_args = dict(unit="ms", origin="unix")
        return pd.read_sql(
            "SELECT * FROM distance_record_table",
            self.conn,
            parse_dates={
                "last_modified_time": date_args,
                "start_time": date_args,
                "end_time": date_args,
                "local_date_time_start_time": date_args,
                "local_date_time_end_time": date_args,
            },
            index_col="row_id",
        )

        # TODO:
        # local_date_time has the time zone offset ok but not daylight savings time

    def daily_distance(
        self,
    ) -> pd.Series:
        distance_df = self.distance_table()

        distance_df["local_date"] = distance_df["local_date_time_start_time"].dt.date

        return distance_df.groupby("local_date")["distance"].sum().sort_index()

    def daily_stats(
        self,
    ) -> pd.DataFrame:
        weight_series = self.daily_weight()
        distance_series = self.daily_distance()

        # Merge the two series
        merged_df = pd.merge(weight_series.reset_index(), distance_series.reset_index(), on="local_date", how="outer").sort_index()

        # add cols for readability
        merged_df["weight_lbs"] = merged_df["weight"] * GRAMS_TO_POUNDS

        merged_df["distance_miles"] = merged_df["distance"] * METERS_TO_MILES
        merged_df["distance_miles_7d_sum"] = merged_df["distance_miles"].rolling(7).sum()

        # KM can be useful to compare against Pokemon Go's automated tracking
        merged_df["distance_km"] = merged_df["distance"] / 1000
        merged_df["distance_km_7d_sum"] = merged_df["distance_km"].rolling(7).sum()

        return merged_df


# with HealthConnect("/content/drive/MyDrive/Physical Training/Health Connect.zip") as hc:

#     hc.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = hc.cursor.fetchall()

#     print("Tables in the database and their columns:")
#     for table_name in tables:
#         table_name = table_name[0]
#         num_rows = hc.cursor.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
#         if num_rows < 10:
#             continue


#         print(f"\nTable: {table_name}")
#         print(f"Num rows: {num_rows}")
#         hc.cursor.execute(f"PRAGMA table_info({table_name});")
#         columns = hc.cursor.fetchall()
#         if columns:
#             for col in columns:
#                 print(f"  Column: {col[1]} (Type: {col[2]}, Not Null: {bool(col[3])}, Primary Key: {bool(col[5])})")
#         else:
#             print("  No columns found (or table is empty/does not exist).")

# with HealthConnect("/content/drive/MyDrive/Physical Training/Health Connect.zip") as hc:
#     daily_stats = hc.daily_stats()

# daily_stats.tail(20)
