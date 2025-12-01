from typing import List, Set, Tuple

DEFAULT_OVULATION_FORGIVENESS_WINDOW_DAYS = 3


def compute_accuracy(
    labels: List[str],
    luteal_preds: Set[int],
    warmup_period: int = 0
) -> Tuple[float, int, int]:
    """
    Compute overall classification accuracy for luteal/ovulation vs. follicular.

    A correct prediction means:
        - If true label is 'luteal' or 'ovulation', index must be in luteal_preds.
        - If true label is anything else, index must NOT be in luteal_preds.
        - 'missing' labels are excluded from the accuracy denominator.

    Parameters
    ----------
    labels : List[str]
        Ground-truth phase labels.
    luteal_preds : set of int
        Indices predicted to be luteal or ovulation.
    warmup_period : int, default 0
        Number of initial indices to skip.

    Returns
    -------
    accuracy : float
        Correct predictions / total considered.
    total_correct : int
        Count of correct predictions.
    total_considered : int
        Total valid labels considered (excluding warmup + missing).
    """
    total_correct = 0
    total_missing = 0

    for i in range(warmup_period, len(labels)):
        label = labels[i]

        if label == "missing":
            total_missing += 1
            continue

        if label in ("luteal", "ovulation"):
            if i in luteal_preds:
                total_correct += 1
        else:
            # Anything NOT predicted luteal is considered correct follicular
            if i not in luteal_preds:
                total_correct += 1

    total_considered = len(labels) - warmup_period - total_missing
    print(f"Out of {len(labels)} labels, {total_missing} are missing")

    if total_considered == 0:
        return 0.0, total_correct, total_considered

    return total_correct / total_considered, total_correct, total_considered


def compute_ovulation_accuracy(
    labels: List[str],
    ovulation_preds: Set[int],
    warmup_period: int = 0,
    ovulation_forgiveness_window_days: int = DEFAULT_OVULATION_FORGIVENESS_WINDOW_DAYS
) -> Tuple[float, int, int]:
    """
    Compute ovulation prediction accuracy using a forgiveness window.
    If any prediction falls within +/- forgiveness_window days
    around a true 'ovulation' label, it is counted as correct.

    Parameters
    ----------
    labels : List[str]
        Ground-truth labels.
    ovulation_preds : set of int
        Indices predicted as ovulation.
    warmup_period : int, default 0
        Ignore labels before this index.
    ovulation_forgiveness_window_days : int, default 3
        Window around prediction to accept as correct.

    Returns
    -------
    accuracy : float
    total_correct : int
    total_considered : int  # number of true ovulation labels
    """
    total_correct = 0

    # Count true ovulation labels in the considered region
    total_considered = labels[warmup_period:].count("ovulation")

    if total_considered == 0:
        return 0.0, 0, 0

    for pred_idx in ovulation_preds:
        # Check window bounds
        start = max(warmup_period, pred_idx - ovulation_forgiveness_window_days)
        end = min(len(labels) - 1, pred_idx + ovulation_forgiveness_window_days)

        for j in range(start, end + 1):
            if labels[j] == "ovulation":
                total_correct += 1
                break

    accuracy = total_correct / total_considered
    return accuracy, total_correct, total_considered


def compute_fertility_accuracy(
    labels: List[str],
    fertility_preds: Set[int],
    warmup_period: int = 0
) -> Tuple[float, int, int]:
    """
    Compute accuracy of fertility predictions.
    A prediction is correct if the index's label is 'ovulation' or 'fertile'.

    Parameters
    ----------
    labels : List[str]
        Ground-truth cycle phase labels.
    fertility_preds : set of int
        Predicted fertile/ovulation indices.
    warmup_period : int, default 0
        Ignore labels before this index.

    Returns
    -------
    accuracy : float
    total_correct : int
    total_considered : int  # true ovulation + fertile labels
    """
    total_correct = 0

    # Count ground-truth fertile-related labels
    total_considered = (
        labels[warmup_period:].count("ovulation") +
        labels[warmup_period:].count("fertile")
    )

    if total_considered == 0:
        return 0.0, 0, 0

    for idx in fertility_preds:
        if labels[idx] in ("ovulation", "fertile"):
            total_correct += 1

    accuracy = total_correct / total_considered
    return accuracy, total_correct, total_considered
