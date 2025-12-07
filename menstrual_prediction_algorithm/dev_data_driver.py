"""
Entry point for running menstrual cycle prediction accuracy evaluation.

This script:
1. Loads processed physiological and label data.
2. Runs the weighted-window ovulation-adjusted prediction algorithm.
3. Prints accuracy statistics.

Requires:
    - data_loading.load_processed_data
    - menstrual_cycle_prediction.compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy
"""

from typing import Tuple
from data_loading import load_processed_data
from menstrual_cycle_prediction import (
    compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy
)


def main() -> None:
    """
    Load cleaned physiological data and evaluate menstrual cycle prediction accuracy.

    Prints:
        total_correct, total_considered, and accuracy fraction.
    """
    # Load input data
    try:
        temp_data, min_hr_data, labels, dates = load_processed_data()
    except Exception as e:
        raise RuntimeError("Failed to load processed data.") from e

    # Run prediction algorithm
    try:
        accuracy, total_correct, total_considered = (
            compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy(
                temp_data,
                labels,
                visualize=True,
                generate_labels=False
            )
        )
    except Exception as e:
        raise RuntimeError(
            "Prediction evaluation failed. Check data format and prediction function."
        ) from e

    # Output results
    print(
        f"{total_correct} out of {total_considered} correct "
        f"(accuracy = {accuracy:.4f})"
    )


if __name__ == "__main__":
    main()
