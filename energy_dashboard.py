import os
from pathlib import Path
import logging
from typing import List, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ----------------- CONFIG -----------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_FILE = OUTPUT_DIR / "energy_dashboard.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ----------------- TASK 3: OOP MODEL -----------------
class MeterReading:
    def __init__(self, timestamp: pd.Timestamp, kwh: float):
        self.timestamp = timestamp
        self.kwh = kwh


class Building:
    def __init__(self, name: str):
        self.name = name
        self.meter_readings: List[MeterReading] = []

    def add_reading(self, reading: MeterReading):
        self.meter_readings.append(reading)

    def calculate_total_consumption(self) -> float:
        return float(sum(r.kwh for r in self.meter_readings))

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "building": self.name,
                "timestamp": [r.timestamp for r in self.meter_readings],
                "kwh": [r.kwh for r in self.meter_readings],
            }
        )

    def generate_report(self) -> Dict[str, float]:
        df = self.to_dataframe()
        total = df["kwh"].sum()
        mean = df["kwh"].mean()
        min_val = df["kwh"].min()
        max_val = df["kwh"].max()
        return {
            "building": self.name,
            "total_kwh": float(total),
            "mean_kwh": float(mean),
            "min_kwh": float(min_val),
            "max_kwh": float(max_val),
        }


class BuildingManager:
    def __init__(self):
        self.buildings: Dict[str, Building] = {}

    def get_or_create_building(self, name: str) -> Building:
        if name not in self.buildings:
            self.buildings[name] = Building(name)
        return self.buildings[name]

    def from_dataframe(self, df: pd.DataFrame):
        for _, row in df.iterrows():
            b = self.get_or_create_building(row["building"])
            b.add_reading(MeterReading(row["timestamp"], row["kwh"]))

    def generate_all_reports(self) -> pd.DataFrame:
        reports = [b.generate_report() for b in self.buildings.values()]
        return pd.DataFrame(reports)


# ----------------- TASK 1: DATA INGESTION & VALIDATION -----------------
def load_energy_data(data_dir: Path) -> pd.DataFrame:
    logging.info(f"Starting data ingestion from: {data_dir}")
    all_frames = []

    if not data_dir.exists():
        logging.error(f"Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    for file in data_dir.glob("*.csv"):
        try:
            logging.info(f"Reading file: {file.name}")
            df = pd.read_csv(file, on_bad_lines="skip")  # skip illeagel lines

            # ensure required columns
            if "timestamp" not in df.columns or "kwh" not in df.columns:
                logging.warning(f"File {file.name} missing required columns, skipping")
                continue

            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp", "kwh"])

            building_name = file.stem.replace("_", " ").title()
            df["building"] = building_name

            all_frames.append(df)
        except FileNotFoundError:
            logging.error(f"File not found: {file.name}")
        except Exception as e:
            logging.error(f"Error reading {file.name}: {e}")

    if not all_frames:
        raise ValueError("No valid CSV files were loaded from data directory.")

    df_combined = pd.concat(all_frames, ignore_index=True)
    df_combined.sort_values("timestamp", inplace=True)
    logging.info(f"Combined dataframe shape: {df_combined.shape}")
    return df_combined


# ----------------- TASK 2: AGGREGATION LOGIC -----------------
def calculate_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index("timestamp")
    daily = (
        df.groupby("building")["kwh"]
        .resample("D")
        .sum()
        .reset_index()
        .rename(columns={"kwh": "daily_kwh"})
    )
    return daily


def calculate_weekly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index("timestamp")
    weekly = (
        df.groupby("building")["kwh"]
        .resample("W")
        .sum()
        .reset_index()
        .rename(columns={"kwh": "weekly_kwh"})
    )
    return weekly


def building_wise_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("building")["kwh"]
        .agg(["mean", "min", "max", "sum"])
        .reset_index()
        .rename(
            columns={
                "mean": "mean_kwh",
                "min": "min_kwh",
                "max": "max_kwh",
                "sum": "total_kwh",
            }
        )
    )
    return summary


# ----------------- TASK 4: VISUAL OUTPUT -----------------
def create_dashboard_figure(
    daily: pd.DataFrame, weekly: pd.DataFrame, df: pd.DataFrame, out_path: Path
):
    fig, axes = plt.subplots(3, 1, figsize=(12, 14))

    # Line: daily consumption trend for all buildings
    for b_name, group in daily.groupby("building"):
        axes[0].plot(group["timestamp"], group["daily_kwh"], label=b_name)
    axes[0].set_title("Daily Energy Consumption - K.R. Mangalam University")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Daily kWh")
    axes[0].legend()
    axes[0].grid(True)

    # Bar: average weekly usage across buildings
    weekly_mean = (
        weekly.groupby("building")["weekly_kwh"].mean().reset_index()
    )
    axes[1].bar(weekly_mean["building"], weekly_mean["weekly_kwh"])
    axes[1].set_title("Average Weekly Energy Use by Building")
    axes[1].set_xlabel("Building")
    axes[1].set_ylabel("Average Weekly kWh")
    axes[1].tick_params(axis="x", rotation=15)

    # Scatter: peak-hour consumption vs time
    # Peak-hour consumption by hour of day instead of timestamp
    idx = df.groupby("building")["kwh"].idxmax()
    peaks = df.loc[idx].copy()

    # Extract hour to fix x-axis
    peaks["hour"] = peaks["timestamp"].dt.hour

    axes[2].scatter(peaks["hour"], peaks["kwh"])

    # Add labels
    for _, row in peaks.iterrows():
        axes[2].annotate(
            row["building"],
            (row["hour"], row["kwh"]),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=8,
        )

    axes[2].set_title("Peak-Hour Consumption per Building")
    axes[2].set_xlabel("Hour of Day")
    axes[2].set_ylabel("kWh at Peak Hour")
    axes[2].set_xticks(range(0, 24))
    axes[2].grid(True)

    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    logging.info(f"Dashboard saved to {out_path}")


# ----------------- TASK 5: PERSISTENCE & SUMMARY -----------------
def export_results(
    df_clean: pd.DataFrame,
    building_summary: pd.DataFrame,
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
):
    cleaned_path = OUTPUT_DIR / "cleaned_energy_data.csv"
    summary_path = OUTPUT_DIR / "building_summary.csv"

    df_clean.to_csv(cleaned_path, index=False)
    building_summary.to_csv(summary_path, index=False)

    logging.info(f"Cleaned data saved to {cleaned_path}")
    logging.info(f"Building summary saved to {summary_path}")

    # Campus-level summary
    total_campus_kwh = df_clean["kwh"].sum()
    highest_building = building_summary.sort_values(
        "total_kwh", ascending=False
    ).iloc[0]

    # Peak load time
    peak_row = df_clean.loc[df_clean["kwh"].idxmax()]

    # Simple trend messages
    daily_mean = daily["daily_kwh"].mean()
    weekly_mean = weekly["weekly_kwh"].mean()

    summary_lines = [
        "Campus Energy Use Summary - K.R. Mangalam University",
        "--------------------------------------------------",
        f"Total campus consumption (period): {total_campus_kwh:.2f} kWh",
        f"Highest consuming building: {highest_building['building']} "
        f"({highest_building['total_kwh']:.2f} kWh)",
        f"Peak load timestamp: {peak_row['timestamp']} "
        f"({peak_row['kwh']:.2f} kWh)",
        "",
        f"Average daily load (all buildings combined): {daily_mean:.2f} kWh",
        f"Average weekly load (all buildings combined): {weekly_mean:.2f} kWh",
        "",
        "Observation: Daily usage is generally higher on working days and ",
        "drops slightly on weekends. Buildings like Engineering Block and ",
        "Hostel show consistently higher energy use compared to Admin Block ",
        "and Library, indicating lab equipment and residential usage.",
    ]

    summary_text = "\n".join(summary_lines)
    summary_file = OUTPUT_DIR / "summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_text)

    print("\n" + summary_text)
    logging.info(f"Summary report saved to {summary_file}")


# ----------------- MAIN DRIVER -----------------
def main():
    logging.info("=== Campus Energy Dashboard Script Started ===")

    # Task 1: Load & validate
    df_combined = load_energy_data(DATA_DIR)

    # Task 2: Aggregations
    daily_totals = calculate_daily_totals(df_combined.copy())
    weekly_aggregates = calculate_weekly_aggregates(df_combined.copy())
    building_summary = building_wise_summary(df_combined.copy())

    # Task 3: OOP usage (optional but demonstrates structure)
    manager = BuildingManager()
    df_for_oop = df_combined.copy()
    manager.from_dataframe(df_for_oop)
    reports_df = manager.generate_all_reports()
    logging.info("OOP Reports:\n" + str(reports_df))

    # Task 4: Dashboard figure
    dashboard_path = OUTPUT_DIR / "dashboard.png"
    create_dashboard_figure(
        daily_totals, weekly_aggregates, df_combined.copy(), dashboard_path
    )

    # Task 5: Persistence & summary
    export_results(df_combined, building_summary, daily_totals, weekly_aggregates)

    logging.info("=== Campus Energy Dashboard Script Finished ===")


if __name__ == "__main__":
    main()
