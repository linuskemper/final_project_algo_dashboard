from pathlib import Path

import pandas as pd
import yfinance as yf

START_DATE = "2020-01-01"
END_DATE = "2024-12-31"


def download_bitcoin_history(
    ticker: str = "BTC-USD",
    start_date: str = START_DATE,
    end_date: str = END_DATE,
) -> pd.DataFrame:
    """
    Download historical Bitcoin price data from yfinance.
    """
    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        progress=False,
        auto_adjust=False,
    )

    if data.empty:
        raise ValueError("No Bitcoin data downloaded from yfinance.")

    data = data.reset_index()

    # yfinance can return MultiIndex columns for a single ticker
    # (level 0 = price field, level 1 = ticker). Flatten to a single level.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Date", "Close"]].rename(columns={"Close": "close"})
    data["Date"] = pd.to_datetime(data["Date"])
    return data


def load_fear_greed_index(
    csv_path: str | Path,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
) -> pd.DataFrame:
    """
    Load Fear & Greed index data from the CSV file.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Fear & Greed CSV file not found at: {csv_path}"
        )

    df = pd.read_csv(csv_path)

    if "date" in df.columns:
        date_col = "date"
    elif "timestamp" in df.columns:
        date_col = "timestamp"
    else:
        raise ValueError(
            "Fear & Greed CSV must contain a 'date' or 'timestamp' column."
        )

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.rename(
        columns={
            date_col: "date",
            "value": "fg_value",
            "value_classification": "fg_classification",
        }
    )

    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    df = df.loc[mask].copy()
    df = df.sort_values("date").reset_index(drop=True)
    return df