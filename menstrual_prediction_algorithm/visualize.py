import matplotlib.pyplot as plt
from typing import Iterable, List


def plot_curve_pairs(
    data1: Iterable[float],
    data2: Iterable[float],
    label1: str,
    label2: str,
) -> None:
    """
    Plot two curves against the same x-axis but with separate y-axes.

    Parameters
    ----------
    data1 : Iterable[float]
        First data sequence.
    data2 : Iterable[float]
        Second data sequence.
    label1 : str
        Label for the first data series (left y-axis).
    label2 : str
        Label for the second data series (right y-axis).
    """
    fig, ax_left = plt.subplots()

    # Left axis curve
    ax_left.plot(data1, color="blue", label=label1)
    ax_left.set_xlabel("Day")
    ax_left.set_ylabel(label1, color="blue")
    ax_left.tick_params(axis="y", labelcolor="blue")

    # Right axis curve
    ax_right = ax_left.twinx()
    ax_right.plot(data2, color="red", linestyle="--", label=label2)
    ax_right.set_ylabel(label2, color="red")
    ax_right.tick_params(axis="y", labelcolor="red")

    # Combined legend
    left_lines, left_labels = ax_left.get_legend_handles_labels()
    right_lines, right_labels = ax_right.get_legend_handles_labels()
    ax_right.legend(
        left_lines + right_lines,
        left_labels + right_labels,
        loc="upper left",
    )

    plt.title(f"{label1} vs {label2}")
    plt.tight_layout()
    plt.show()


def graph_stacked_with_highlights(
    data0: Iterable[float],
    spikes0: List[int],
    data1: Iterable[float],
    spikes1: List[int],
    data0Name: str = "data0",
    data1Name: str = "data1",
) -> None:
    """
    Plot two aligned stacked time-series curves with vertical lines marking spike indices.

    Parameters
    ----------
    data0 : Iterable[float]
        First dataset.
    spikes0 : List[int]
        Spike indices for first dataset.
    data1 : Iterable[float]
        Second dataset.
    spikes1 : List[int]
        Spike indices for second dataset.
    data0Name : str
        Title for the first plot.
    data1Name : str
        Title for the second plot.
    """
    fig, (ax_top, ax_bottom) = plt.subplots(
        nrows=2, ncols=1, sharex=True, figsize=(10, 6)
    )

    # Top plot
    ax_top.plot(data0, color="blue")
    ax_top.set_title(data0Name)

    for idx in spikes0:
        ax_top.axvline(x=idx, color="red", linestyle="-", linewidth=1.5)

    # Bottom plot
    ax_bottom.plot(data1, color="orange")
    ax_bottom.set_title(data1Name)

    for idx in spikes1:
        ax_bottom.axvline(x=idx, color="green", linestyle="-", linewidth=1.5)

    plt.tight_layout()
    plt.show()


def display_labels(
    true_labels: Iterable[str],
    generated_labels: Iterable[str],
    starting_day: int = 0,
) -> None:
    """
    Print expected vs predicted label comparisons starting at a given index.

    Parameters
    ----------
    true_labels : Iterable[str]
        Ground truth labels.
    generated_labels : Iterable[str]
        Predicted/generated labels.
    starting_day : int
        Index to begin printing comparisons.
    """
    true_labels = list(true_labels)
    generated_labels = list(generated_labels)

    print("\nDay    Expected           Predicted")
    print("----------------------------------------")

    for i, (t, g) in enumerate(zip(true_labels, generated_labels)):
        if i >= starting_day:
            print(f"{i:<6}{t:<18}{g}")
