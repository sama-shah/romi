from typing import Iterable, List


def identify_windowed_spikes(data: Iterable[float], n: int = 14) -> List[int]:
    """
    Identify indices where a value exceeds the average of the previous `n` samples.

    A sliding window is maintained. For each index i >= n:
      - Compute the window average of data[i-n : i].
      - If data[i] > window_average, record the index as a spike.

    Parameters
    ----------
    data : Iterable[float]
        Sequence of numeric samples.
    n : int, optional
        Size of the sliding window used to compute the average.
        Default is 14.

    Returns
    -------
    List[int]
        List of indices where spikes occurred.

    Notes
    -----
    - Uses O(1) incremental updates for the window sum.
    - If `n` is greater than the length of the dataset, returns an empty list.
    """
    data = list(data)
    if n <= 0 or len(data) < n:
        return []

    window_sum = sum(data[:n])
    spike_indices = []

    for i in range(n, len(data)):
        window_avg = window_sum / n

        if data[i] > window_avg:
            spike_indices.append(i)

        # Slide the window forward
        window_sum += data[i] - data[i - n]

    return spike_indices


def identify_weighted_windowed_spikes(data: Iterable[float], n: int = 14) -> List[int]:
    """
    Identify spikes using a dynamic threshold based on a weighted sliding window.

    This variant applies a weight to the window average:
      - Before a run of spikes begins, the threshold is *higher* to avoid
        triggering prematurely.
      - After a run begins, the threshold is *lower* to encourage detecting
        the tail end of the run.

    Weight Behavior:
      - run_weight = (current_run_length / n)
      - Before a spike run starts: threshold multiplier = 2 - run_weight
      - During a spike run:       threshold multiplier = run_weight

    Parameters
    ----------
    data : Iterable[float]
        Sequence of numeric samples.
    n : int, optional
        Window size for the rolling average. Default is 14.

    Returns
    -------
    List[int]
        List of indices where spikes occur based on the adaptive threshold.

    Notes
    -----
    - Maintains O(1) window updates.
    - Tracks "spike runs" to adaptively raise/lower threshold.
    - If `n` is greater than dataset length, returns an empty list.
    """
    data = list(data)
    if n <= 0 or len(data) < n:
        return []

    window_sum = sum(data[:n])
    spike_indices = []

    in_run = False
    run_length = n  # Incentivizes run behavior around window size

    for i in range(n, len(data)):
        base_avg = window_sum / n
        run_weight = run_length / n

        # Adjust threshold based on run status
        if in_run:
            threshold_multiplier = run_weight       # lower threshold during run
        else:
            threshold_multiplier = 2 - run_weight   # higher threshold before run

        threshold = threshold_multiplier * base_avg

        if data[i] > threshold:
            if not in_run:
                in_run = True
                run_length = 0
            spike_indices.append(i)
        elif in_run:
            # End of run
            in_run = False
            run_length = 0

        # Slide the window
        window_sum += data[i] - data[i - n]
        run_length += 1

    return spike_indices
