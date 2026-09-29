"""
ETL script for the Fitness Analytics case study.

Reads the raw Fitabase CSV exports, cleans them, joins them into
analysis-ready tables, and writes everything into a single SQLite
database (fitness.db) that the Streamlit app reads from.

Usage:
    python etl.py --data-dir "./data/Fitabase Data 4.12.16-5.12.16" --out fitness.db
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


def load_daily_activity(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "dailyActivity_merged.csv")
    df["ActivityDate"] = pd.to_datetime(df["ActivityDate"], format="%m/%d/%Y")
    df = df.rename(columns={"ActivityDate": "Date"})

    # dailyCalories / dailyIntensities / dailySteps are redundant subsets
    # of dailyActivity_merged, so they are intentionally not loaded here.

    before = len(df)
    df = df.drop_duplicates()
    dupes_removed = before - len(df)

    zero_activity_days = int((df["TotalSteps"] == 0).sum())
    df["device_worn"] = df["TotalSteps"] > 0  # flag likely non-wear days, keep the rows

    print(f"[daily_activity] rows={len(df)} duplicates_removed={dupes_removed} "
          f"zero_step_days_flagged={zero_activity_days}")
    return df


def load_sleep(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "sleepDay_merged.csv")
    df["SleepDay"] = pd.to_datetime(df["SleepDay"], format="%m/%d/%Y %I:%M:%S %p").dt.normalize()
    df = df.rename(columns={"SleepDay": "Date"})

    before = len(df)
    df = df.drop_duplicates()
    dupes_removed = before - len(df)

    # A handful of Id/Date pairs have more than one sleep record (naps).
    # Sum minutes asleep/in bed, sum records, keep one row per Id/Date.
    df = (
        df.groupby(["Id", "Date"], as_index=False)
        .agg(
            TotalSleepRecords=("TotalSleepRecords", "sum"),
            TotalMinutesAsleep=("TotalMinutesAsleep", "sum"),
            TotalTimeInBed=("TotalTimeInBed", "sum"),
        )
    )
    print(f"[sleep] rows={len(df)} exact_duplicates_removed={dupes_removed} "
          f"(multi-record days collapsed by summing minutes)")
    return df


def load_weight(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "weightLogInfo_merged.csv")
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y %I:%M:%S %p").dt.normalize()
    # Fat is >95% missing (only 2 of 67 rows populated) - not usable, dropped.
    df = df.drop(columns=["Fat"], errors="ignore")
    df = df.drop_duplicates()
    print(f"[weight] rows={len(df)} users={df['Id'].nunique()} "
          f"(sparse: only {df['Id'].nunique()} of 33 users logged weight)")
    return df


def load_heartrate_daily(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "heartrate_seconds_merged.csv")
    df["Time"] = pd.to_datetime(df["Time"], format="%m/%d/%Y %I:%M:%S %p")
    df["Date"] = df["Time"].dt.normalize()

    daily = (
        df.groupby(["Id", "Date"], as_index=False)["Value"]
        .agg(AvgHeartRate="mean", MinHeartRate="min", MaxHeartRate="max")
    )
    print(f"[heartrate] raw_rows={len(df)} aggregated_to_daily_rows={len(daily)} "
          f"users={daily['Id'].nunique()} (per-second data aggregated to daily "
          f"avg/min/max - raw granularity is too heavy for the dashboard)")
    return daily


def load_hourly(data_dir: Path) -> pd.DataFrame:
    cal = pd.read_csv(data_dir / "hourlyCalories_merged.csv")
    inten = pd.read_csv(data_dir / "hourlyIntensities_merged.csv")
    steps = pd.read_csv(data_dir / "hourlySteps_merged.csv")

    for d in (cal, inten, steps):
        d["ActivityHour"] = pd.to_datetime(d["ActivityHour"], format="%m/%d/%Y %I:%M:%S %p")

    merged = cal.merge(inten, on=["Id", "ActivityHour"], how="outer")
    merged = merged.merge(steps, on=["Id", "ActivityHour"], how="outer")
    print(f"[hourly] rows={len(merged)} (calories + intensities + steps merged on Id/hour)")
    return merged


def build_daily_master(activity, sleep, hr_daily, weight) -> pd.DataFrame:
    master = activity.merge(sleep, on=["Id", "Date"], how="left")
    master = master.merge(hr_daily, on=["Id", "Date"], how="left")
    master = master.merge(weight[["Id", "Date", "WeightKg", "BMI"]], on=["Id", "Date"], how="left")
    print(f"[daily_master] rows={len(master)} columns={len(master.columns)} "
          f"(left-joined on daily activity as the base table)")
    return master


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Path to the folder with the raw Fitabase CSVs")
    parser.add_argument("--out", default="fitness.db", help="Output SQLite database path")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    activity = load_daily_activity(data_dir)
    sleep = load_sleep(data_dir)
    weight = load_weight(data_dir)
    hr_daily = load_heartrate_daily(data_dir)
    hourly = load_hourly(data_dir)
    daily_master = build_daily_master(activity, sleep, hr_daily, weight)

    out_path = Path(args.out)
    conn = sqlite3.connect(out_path)
    daily_master.to_sql("daily_master", conn, if_exists="replace", index=False)
    activity.to_sql("daily_activity", conn, if_exists="replace", index=False)
    sleep.to_sql("sleep", conn, if_exists="replace", index=False)
    weight.to_sql("weight", conn, if_exists="replace", index=False)
    hr_daily.to_sql("heartrate_daily", conn, if_exists="replace", index=False)
    hourly.to_sql("hourly", conn, if_exists="replace", index=False)
    conn.close()

    print(f"\nDone. Wrote tables [daily_master, daily_activity, sleep, weight, "
          f"heartrate_daily, hourly] to {out_path.resolve()}")


if __name__ == "__main__":
    main()
