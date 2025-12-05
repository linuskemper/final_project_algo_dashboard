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
