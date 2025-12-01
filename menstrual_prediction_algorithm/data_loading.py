import ast
import warnings
from typing import List, Tuple, Dict

import pandas as pd
from data_processing_utils import remove_nan, str_to_date, weighted_past_average


def load_raw_data() -> Tuple[List, List[float], List[float]]:
    """
    Load and preprocess raw data for temperature deviation and min heart rate

    Returns
    -------
    dates : List
        List of Python date objects parsed from the raw CSV.
    temp_data : List[float]
        Temperature deviation values, filling missing entries using a
        weighted past average (n=3).
    min_hr_data : List[float]
        Cleaned list of minimum heart-rate values with NaNs removed.
    """
    df = pd.read_csv("../raw_data/sleep_2024-03-22_2025-09-16.csv")

    # Parse dates
    dates = df["day"].apply(str_to_date).tolist()

    # Clean heart data
    min_hr_data = remove_nan(df["lowest_heart_rate"]).tolist()

    # Readiness column contains temperature deviation inside a dictionary-like string
    readiness_entries = df["readiness"]

    temp_data: List[float] = []

    for entry in readiness_entries:
        try:
            if isinstance(entry, str):
                parsed = ast.literal_eval(entry)
                temp = parsed.get("temperature_deviation")

                if temp is not None and temp != "":
                    temp_data.append(temp)
                else:
                    # Missing → fill using past n=3 weighted average
                    temp_data.append(weighted_past_average(temp_data, n=3))
            else:
                # Non-string entry → fallback
                warnings.warn("Non-string readiness entry encountered; filling with weighted average.")
                temp_data.append(weighted_past_average(temp_data, n=3))

        except (ValueError, SyntaxError) as e:
            warnings.warn(f"Failed to parse readiness entry: {entry!r}. Error: {e}")
            temp_data.append(weighted_past_average(temp_data, n=3))

    return dates, temp_data, min_hr_data

def load_truth_map() -> Dict:
    """
    Load ground-truth phase labels and map them to date keys.

    Returns
    -------
    truth_mapping : dict
        Dictionary mapping Python date objects → string phase labels.
    """
    truth_df = pd.read_csv("../calendar_data_full_annotated.csv")
    truth_mapping = {}

    for date_str, label in zip(truth_df["day"], truth_df["phase"]):
        truth_mapping[str_to_date(date_str)] = label

    return truth_mapping

def load_processed_data() -> Tuple[List[float], List[float], List[str], List]:
    """
    Load fully processed data: temperature deviation, heart rate, labels, and dates.

    Returns
    -------
    temp_data : List[float]
        Cleaned temperature deviation series.
    min_hr_data : List[float]
        Cleaned minimum heart-rate series.
    labels : List[str]
        Ground-truth phase labels aligned with dates.
        If a date is missing in the truth map, label is "missing".
    dates : List
        List of Python date objects.
    """
    dates, temp_data, min_hr_data = load_raw_data()
    truth_map = load_truth_map()

    labels: List[str] = []

    for date in dates:
        if date in truth_map:
            labels.append(truth_map[date])
        else:
            warnings.warn(f"No truth label found for date {date}; assigning 'missing'.")
            labels.append("missing")

    return temp_data, min_hr_data, labels, dates
