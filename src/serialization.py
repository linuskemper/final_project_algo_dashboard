import pandas as pd

def to_list_safe(series):
    """ Converts a Pandas Series to a list, handling NaNs by replacing them """
    return [None if pd.isna(x) else x for x in series.tolist()]

def serialize_data(df):
    """ Serializes the dataframe for the API """
    data_dict = {}

    # Create valid date string
    data_dict["dates"] = [d.strftime("%Y-%m-%d") for d in df.index]

    # Convert price series to list
    if "close" in df.columns:
        data_dict["prices"] = to_list_safe(df["close"])

    return data_dict