import matplotlib.pyplot as plt

def plot_curve_pairs(data1, data2, label1, label2):
    # Create the first plot with the left y-axis
    fig, ax1 = plt.subplots()

    ax1.plot(data1, 'b-', label=label1)
    ax1.set_xlabel('Day')
    ax1.set_ylabel(label1, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create a twin Axes for the right y-axis
    ax2 = ax1.twinx()

    ax2.plot(data2, 'r--', label=label2)
    ax2.set_ylabel(label2, color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Add legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.title(f"{label1} vs. {label2}")
    plt.show()


def graph_stacked_with_highlights(data0, spikes0, data1, spikes1, data0Name='data0', data1Name='data1'):
    # Graph preds on separate graphs for comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True) 

    # Plot on the first (top) subplot
    ax1.plot(data0, color='blue')
    ax1.set_title(data0Name)
    # ax1.set_ylabel('temp')

    for spike in spikes0:
        ax1.axvline(x=spike, color='r', linestyle='-', linewidth=2)

    # Plot on the second (bottom) subplot
    ax2.plot(data1, color='red')
    ax2.set_title(data1Name)
    # ax2.set_ylabel('hr')

    for spike in spikes1:
        plt.axvline(x=spike, color='g', linestyle='-', linewidth=2)

    # Adjust layout to prevent labels from overlapping
    plt.tight_layout()

    # Display the plot
    plt.show()

def display_labels(true_labels, generated_labels, starting_day):
    col_width = 15
    print("\t Expected   Predicted")
    for i, (true_label, generated) in enumerate(zip(true_labels, generated_labels)):
        if(i >= starting_day):
            print(f"Day {i}: {true_label:<{col_width}} {generated}")

