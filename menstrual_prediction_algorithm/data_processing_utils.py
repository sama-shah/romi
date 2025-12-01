from datetime import date
from typing import List, Dict, Iterable, Tuple, Set, Optional
import pandas as pd


def str_to_date(string: str) -> date:
    """
    Convert a string in 'YYYY-MM-DD' format to a `datetime.date` object.

    Parameters
    ----------
    string : str
        Date string in ISO format.

    Returns
    -------
    date
        Parsed Python date object.

    Raises
    ------
    ValueError
        If the string is not in a valid YYYY-MM-DD format.
    """
    try:
        year, month, day = map(int, string.split("-"))
        return date(year, month, day)
    except Exception as e:
        raise ValueError(f"Invalid date string: {string}") from e


def phase_from_date(phases: Dict[str, str], dt: date) -> Optional[str]:
    """
    Look up the phase label for a given date.

    Parameters
    ----------
    phases : dict
        Mapping from 'YYYY-MM-DD' → phase label.
    dt : date
        A Python `date` object.

    Returns
    -------
    str or None
        The phase label if found, otherwise None.
    """
    return phases.get(dt.strftime("%Y-%m-%d"))


def low_pass(data: Iterable[float], window_size: int = 3) -> List[float]:
    """
    Apply a simple moving-average low-pass filter.

    Parameters
    ----------
    data : Iterable[float]
        Input numeric series.
    window_size : int, default 3
        Size of smoothing window.

    Returns
    -------
    List[float]
        Smoothed data, length = len(data) - window_size.
    """
    data = list(data)
    if window_size <= 0:
        raise ValueError("window_size must be positive")

    return [
        sum(data[i:i + window_size]) / window_size
        for i in range(len(data) - window_size)
    ]


def weighted_past_average(data: List[float], n: int = 3) -> float:
    """
    Compute a weighted average over the last `n` values of a list, with
    newer values weighted more heavily.

    Weights: n, n-1, ..., 1 (linearly decreasing)

    Parameters
    ----------
    data : List[float]
        Historical data points.
    n : int, default 3
        Number of past points to use.

    Returns
    -------
    float
        Weighted average value.

    Raises
    ------
    ValueError
        If there are fewer than `n` data points available.
    """
    if len(data) < n:
        raise ValueError(f"Not enough history: {len(data)} values available, {n} required.")

    total = 0
    for i in range(n):
        weight = n - i
        total += weight * data[-1 - i]

    return 2 * total / (n * (n + 1))  # Normalizing constant


def remove_nan(series: pd.Series, n: int = 3) -> pd.Series:
    """
    Replace NaN values in a pandas Series using weighted past average.

    Parameters
    ----------
    series : pd.Series
        Time-series data.
    n : int, default 3
        Number of past values used for imputation.

    Returns
    -------
    pd.Series
        Series with NaNs filled.

    Notes
    -----
    - If the first NaNs occur before at least `n` previous values exist,
      the function raises an error.
    """
    series = series.copy()

    for idx in series[series.isna()].index:
        history = series[idx - n:idx].tolist()

        if len(history) < n or any(pd.isna(history)):
            raise ValueError(
                f"Cannot compute weighted_past_average for index {idx}: "
                f"requires {n} valid past values."
            )

        series.loc[idx] = weighted_past_average(history, n=n)

    return series


def compute_confusion_matrix(
    true_labels: Set[int],
    pred_labels: Set[int],
    total_data_size: int
) -> Tuple[List[int], List[int], List[int], List[int], List[str]]:
    """
    Compute a simple confusion matrix for binary classification where
    labels indicate indices belonging to the positive class.

    Parameters
    ----------
    true_labels : set of int
        Indices of true-positive class.
    pred_labels : set of int
        Indices predicted as positive.
    total_data_size : int
        Total number of data points.

    Returns
    -------
    TN, TP, FP, FN : Lists of indices
    streamed_matrix : List[str]
        Per-index label: 'TP', 'TN', 'FP', 'FN'
    """
    TN, TP, FP, FN = [], [], [], []
    streamed = []

    for i in range(total_data_size):
        truth = i in true_labels
        pred = i in pred_labels

        if truth and pred:
            TP.append(i)
            streamed.append("TP")
        elif truth and not pred:
            FN.append(i)
            streamed.append("FN")
        elif not truth and pred:
            FP.append(i)
            streamed.append("FP")
        else:
            TN.append(i)
            streamed.append("TN")

    return TN, TP, FP, FN, streamed


def create_generated_labels(
    num_data_points: int,
    ovulation: Set[int],
    fertility: Set[int],
    spike: Set[int],
    period: Set[int]
) -> List[str]:
    """
    Generate label strings for each time index based on membership
    in different physiological phase index sets.

    Priority order:
        ovulation → fertile → luteal → period → follicular

    Parameters
    ----------
    num_data_points : int
        Number of data points to label.
    ovulation, fertility, spike, period : set of int
        Sets of indices for each physiological phase.

    Returns
    -------
    List[str]
        A label per data point.
    """
    labels = []

    for i in range(num_data_points):
        if i in ovulation:
            labels.append("ovulation")
        elif i in fertility:
            labels.append("fertile")
        elif i in spike:
            labels.append("luteal")
        elif i in period:
            labels.append("period")
        else:
            labels.append("follicular")

    return labels
