"""
Prediction pipeline for cycle phase detection using spike-based temperature features.
Includes:
    - Basic spike detection
    - Weighted-window spike detection
    - Label-aware period-adjusting spike detection
    - Accuracy computation utilities
    - Optional visualization and label generation
"""

from typing import List, Tuple, Set

from data_processing_utils import low_pass, create_generated_labels
from prediction_primitives import (
    identify_windowed_spikes,
    identify_weighted_windowed_spikes,
)
from accuracy import (
    compute_accuracy,
    compute_fertility_accuracy,
    compute_ovulation_accuracy,
)
from visualize import graph_stacked_with_highlights, display_labels


# --------------------------------------------------------------------------------------
# CONFIGURATION CONSTANTS
# --------------------------------------------------------------------------------------

FERTILE_DAYS_BEFORE_LUTEAL = 6
FERTILE_DAYS_DURING_LUTEAL = 3
PERIOD_LENGTH_DAYS = 5
OVULATION_FORGIVENESS_WINDOW_DAYS = 3


# --------------------------------------------------------------------------------------
# PERIOD-ADJUSTING WEIGHTED WINDOW SPIKE DETECTION
# --------------------------------------------------------------------------------------

def period_adjusting_identify_weighted_windowed_spikes(
    data: List[float],
    labels: List[str],
    n: int = 14
) -> Tuple[List[int], List[int], List[int], List[int]]:
    """
    Label-aware variant of weighted windowed spike detection.

    Behaviors:
        - Detects temperature spikes using a weighted threshold.
        - Period labels reset the run window.
        - Predicts fertility window & ovulation relative to detected spike timing.
        - Predicts "period" window after a spike drop.

    Parameters
    ----------
    data : List[float]
        Smoothed temperature or physiological signal.
    labels : List[str]
        Ground-truth labels for cycle tracking (e.g., follicular, luteal, period).
    n : int, default 14
        Rolling window size used for calculating moving average.

    Returns
    -------
    ovulation_indices : List[int]
    fertility_indices : List[int]
    spike_indices : List[int]       # predicted luteal region
    period_indices : List[int]      # predicted period region
    """

    if len(data) < n:
        return [], [], [], []

    windowed_sum = sum(data[:n])
    spike_indices = []
    ovulation_indices = []
    fertility_indices = []
    period_indices = []

    spiked_run = False

    # Initialize run size (distance since last period)
    if "period" in labels[:n]:
        current_run_size = n - labels.index("period")
    else:
        current_run_size = n

    for i in range(n, len(data)):
        # ------------------------------------------------------------------
        # Predict fertility/ovulation window relative to expected spike day
        # ------------------------------------------------------------------
        fertile_start_target = n - FERTILE_DAYS_BEFORE_LUTEAL

        if current_run_size == fertile_start_target and not spiked_run:
            # Fertile window spans BEFORE + AFTER luteal detection
            fertile_span = FERTILE_DAYS_BEFORE_LUTEAL + FERTILE_DAYS_DURING_LUTEAL

            for offset in range(fertile_span):
                idx = i + offset
                if idx < len(data):
                    fertility_indices.append(idx)

            # Ovulation roughly in the middle of fertile window
            ov_idx = i + FERTILE_DAYS_BEFORE_LUTEAL
            if ov_idx < len(data):
                ovulation_indices.append(ov_idx)

        # ------------------------------------------------------------------
        # Weighted threshold calculation
        # ------------------------------------------------------------------
        run_weight = current_run_size / n
        run_weight = run_weight if spiked_run else (2 - run_weight)

        threshold = run_weight * (windowed_sum / n)

        # ------------------------------------------------------------------
        # Spike detection logic
        # ------------------------------------------------------------------
        if data[i] > threshold:
            # Spike begins
            if not spiked_run:
                spiked_run = True
                current_run_size = 0
            spike_indices.append(i)

        else:
            # Spike ends — predict period region
            if spiked_run:
                spiked_run = False
                for offset in range(PERIOD_LENGTH_DAYS):
                    idx = i + offset
                    if idx < len(data):
                        period_indices.append(idx)
                current_run_size = 0

        # ------------------------------------------------------------------
        # Rolling window update
        # ------------------------------------------------------------------
        windowed_sum += data[i] - data[i - n]
        current_run_size += 1

        # ------------------------------------------------------------------
        # Recalibrate if user-reported period input appears
        # ------------------------------------------------------------------
        if labels[i - 1] != "period" and labels[i] == "period":
            current_run_size = 1
            spiked_run = False

    return ovulation_indices, fertility_indices, spike_indices, period_indices


# --------------------------------------------------------------------------------------
# BASELINE SPIKE PREDICTIONS
# --------------------------------------------------------------------------------------

def _compute_true_luteal_indices(labels: List[str], window_size: int) -> List[int]:
    """Helper for visualization."""
    return [
        i for i in range(window_size, len(labels))
        if labels[i] in ("luteal", "ovulation")
    ]


def compute_spiked_prediction_accuracy(
    data: List[float],
    labels: List[str],
    window_size: int = 14,
    visualize: bool = True
):
    """
    Compute accuracy using basic spike detection (simple moving average).
    """

    smoothed = low_pass(data, window_size=3)
    spike_indices = identify_windowed_spikes(smoothed, n=window_size)

    accuracy, total_correct, total_considered = compute_accuracy(
        labels, set(spike_indices), warmup_period=window_size
    )

    print(f"Accuracy: {accuracy:.3f}")

    if visualize:
        true_spikes = _compute_true_luteal_indices(labels, window_size)
        graph_stacked_with_highlights(
            smoothed, spike_indices,
            smoothed, true_spikes,
            data0Name="predicted", data1Name="true_label"
        )

    return accuracy, total_correct, total_considered


# --------------------------------------------------------------------------------------
# WEIGHTED WINDOW SPIKE PREDICTION
# --------------------------------------------------------------------------------------

def compute_weighted_window_spiked_prediction_accuracy(
    data: List[float],
    labels: List[str],
    window_size: int = 14,
    visualize: bool = True
):
    """
    Compute accuracy using weighted-window spike detection.
    """

    smoothed = low_pass(data, window_size=3)
    spike_indices = identify_weighted_windowed_spikes(smoothed, n=window_size)

    accuracy, total_correct, total_considered = compute_accuracy(
        labels, set(spike_indices), warmup_period=window_size
    )

    print(f"Accuracy: {accuracy:.3f}")

    if visualize:
        true_spikes = _compute_true_luteal_indices(labels, window_size)
        graph_stacked_with_highlights(
            smoothed, spike_indices,
            smoothed, true_spikes,
            data0Name="predicted", data1Name="true_label"
        )

    return accuracy, total_correct, total_considered


# --------------------------------------------------------------------------------------
# LABEL-AWARE SPIKE PREDICTION (PERIOD ADJUSTING)
# --------------------------------------------------------------------------------------

def compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy(
    data: List[float],
    labels: List[str],
    window_size: int = 14,
    visualize: bool = True,
    generate_labels: bool = False,
):
    """
    Full label-aware spike-based prediction including:
        - Fertility detection
        - Ovulation detection
        - Luteal prediction
        - Period prediction

    When generate_labels is True, generate labels and print mismatches for
    a diagnostic window (window_size .. max_inspect_index).
    """
    smoothed = low_pass(data, window_size=3)

    (
        ovulation_indices,
        fertility_indices,
        spike_indices,
        period_indices,
    ) = period_adjusting_identify_weighted_windowed_spikes(
        smoothed, labels, n=window_size
    )

    # ------------------------------------------------------------------
    # Optional label generation comparison (restores mismatch printing)
    # ------------------------------------------------------------------
    if generate_labels:
        generated_labels = create_generated_labels(
            len(labels),
            ovulation_indices,
            fertility_indices,
            spike_indices,
            period_indices,
        )

        # Show a compact side-by-side printout
        display_labels(labels, generated_labels, window_size)

        # Compare and print mismatches over a diagnostic window:
        # original code compared up to index 198; keep that intent but be safe.
        start = window_size
        end = min(len(labels), 198)  # exclusive upper bound for inspection

        match = 0
        total = 0

        for i in range(start, end):
            truth = labels[i]
            generated = generated_labels[i]
            total += 1

            # Original logic considered period <-> follicular as matching
            if (truth == generated) or (truth == 'period' and generated == 'follicular') or (truth == 'follicular' and generated == 'period'):
                match += 1
            else:
                # Print day relative to the full dataset (matches original style)
                print(f"Day {i}: mismatch -> truth='{truth}' generated='{generated}'")

        if total > 0:
            print(f"{match} matches in range [{start}, {end}) out of {total} "
                  f"for accuracy {match / total:.3f}")
        else:
            print("No days to inspect in the diagnostic range.")

    # ------------------------------------------------------------------
    # Accuracy metrics
    # ------------------------------------------------------------------
    luteal_acc, luteal_corr, luteal_total = compute_accuracy(
        labels, set(spike_indices), warmup_period=window_size
    )

    ovulation_acc, ovu_corr, ovu_total = compute_ovulation_accuracy(
        labels, set(ovulation_indices),
        warmup_period=window_size
    )

    fertility_acc, fert_corr, fert_total = compute_fertility_accuracy(
        labels, set(fertility_indices), warmup_period=window_size
    )

    print(f"Luteal accuracy:    {luteal_acc:.3f}")
    print(f"Ovulation accuracy: {ovulation_acc:.3f}")
    print(f"Fertility accuracy: {fertility_acc:.3f}")

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------
    if visualize:
        true_spikes = _compute_true_luteal_indices(labels, window_size)
        graph_stacked_with_highlights(
            smoothed, spike_indices,
            smoothed, true_spikes,
            data0Name="predicted", data1Name="true_label"
        )

    return luteal_acc, luteal_corr, luteal_total
