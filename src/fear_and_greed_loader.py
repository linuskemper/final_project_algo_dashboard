import csv
from datetime import datetime
from typing import List, Dict

import requests

API_URL = "https://api.alternative.me/fng/"
START_DATE = datetime(2020, 1, 1).date()
END_DATE = datetime(2024, 12, 31).date()
OUTPUT_FILE = "data/fear_greed_2022_2024.csv"


def fetch_fear_greed_data() -> List[Dict]:
    """
    Fetches all available Fear-&-Greed-Data from alternative.me.

    Returns:
        List of Dicts with raw data from API.
    """
    params = {
        "limit": 0,       # 0 = all avalaibale data
        "format": "json",  # set type to JSON
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("data", [])


def filter_by_date(
        data: List[Dict],
        start_date: datetime.date,
        end_date: datetime.date) -> List[Dict]:
    """
    Filters the raw data according to the time frame.

    Returns:
        Filters for date and sorts the list.
    """
    filtered_rows: List[Dict] = []

    for item in data:
        # API-Timestamp is Unix-Time in Sekunden
        timestamp = int(item["timestamp"])
        date = datetime.utcfromtimestamp(timestamp).date()

        if start_date <= date <= end_date:
            filtered_rows.append({
                "date": date.isoformat(),
                "value": item.get("value"),
                "value_classification": item.get("value_classification"),
            })

    # sort the dates
    filtered_rows.sort(key=lambda row: row["date"])
    return filtered_rows


def save_to_csv(rows: List[Dict], filename: str) -> None:
    """
    Writes data from API into a csv.
    """
    fieldnames = ["date", "value", "value_classification"]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
