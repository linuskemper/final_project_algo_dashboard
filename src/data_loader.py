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