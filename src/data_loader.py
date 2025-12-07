"""Data loading and preprocessing utilities for the trading dashboard."""

from pathlib import Path
from typing import Tuple

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


def merge_price_and_sentiment(
    price_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge Bitcoin prices and Fear & Greed sentiment into one data frame.
    """
    price = price_df.copy()
    price = price.rename(columns={"Date": "date"})
    price["date"] = pd.to_datetime(price["date"])
    price = price.sort_values("date").reset_index(drop=True)

    sentiment = sentiment_df.copy()
    sentiment["date"] = pd.to_datetime(sentiment["date"])
    sentiment = sentiment.sort_values("date").reset_index(drop=True)

    # Merge on the explicit date column to avoid MultiIndex join errors.
    merged = price.merge(
        sentiment[["date", "fg_value", "fg_classification"]],
        on="date",
        how="left",
    )
    merged = merged.set_index("date").sort_index()
    merged["fg_value"] = merged["fg_value"].ffill()

    merged = merged.loc[
        (merged.index >= pd.to_datetime(START_DATE))
        & (merged.index <= pd.to_datetime(END_DATE))
    ]

    merged["return"] = merged["close"].pct_change()
    merged = merged.dropna(subset=["return"])
    return merged


def load_all_data(
    fear_greed_csv: str | Path,
    ticker: str = "BTC-USD",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and merge Bitcoin price data with Fear & Greed sentiment.
    """
    price_df = download_bitcoin_history(ticker=ticker)
    sentiment_df = load_fear_greed_index(csv_path=fear_greed_csv)
    merged_df = merge_price_and_sentiment(price_df, sentiment_df)
    return price_df, sentiment_df, merged_df


def get_default_data_paths(base_dir: str | Path) -> Path:
    """
    Return the default path for the Fear & Greed CSV inside the data folder.
    """
    base_path = Path(base_dir)
    return base_path / "data" / "fear_greed_2022_2024.csv"


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    csv_file = get_default_data_paths(project_root)
    print("Using Fear & Greed CSV at:", csv_file)

    btc_df, fg_df, merged = load_all_data(csv_file)
    print("Bitcoin data:", btc_df.head())
    print("Fear & Greed data:", fg_df.head())
    print("Merged data:", merged.head())
