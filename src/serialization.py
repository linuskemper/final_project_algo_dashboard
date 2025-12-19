import pandas as pd
from typing import List

def _to_list_handle_nan(series: pd.Series) -> List:
    """ Converts a Pandas Series to a list, handling NaNs by replacing them """
    return [None if pd.isna(x) else x for x in series.tolist()]

def serialize_data(df):
    """ Serializes the dataframe for the API """
    data_dict = {}

    # Create valid date string
    data_dict["dates"] = [d.strftime("%Y-%m-%d") for d in df.index]

    col_mapping = {
        "close" : "close",
        "sma_short" : "sma_short",
        "sma_long" : "sma_long",
        "bb_middle" : "bb_middle",
        "bb_upper" : "bb_upper",
        "bb_lower" : "bb_lower",
        "fg_value" : "fg_value",
        "kalman_trend" : "kalman_trend"
    }

    for df_col, api_key in col_mapping.items():
        if df_col in df.columns:
            data_dict[api_key] = _to_list_handle_nan(df[df_col])

    # Handle signals separately
    if "trade_signal" in df.columns:
        data_dict["trade_signal"] = df["trade_signal"].fillna("Hold").tolist()

    return data_dict