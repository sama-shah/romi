import pandas as pd
import ast
import matplotlib.pyplot as plt
from datetime import date

FOLLICULAR = 0
LUTEAL = 1
MENSES = 2
OVULATION = 3

# Applies a low pass filter to smooth data with a window size of n
def low_pass(data, window_size=3):
    newData = []
    
    for i in range(len(data) - window_size):
        newData.append(sum(data[i: i + window_size]) / window_size)

    return newData

# Returns the weighted average of the last n values of data
def weighted_past_average(data, n=3):
    average = 0

    for i in range(n):
        average += (n - i) * data[-1 - i]

    average = 2 * average / (n * (n + 1))

    return average

# Removes nans for a pandas series, replacing them with a weighted past average over n values
def remove_nan(data, n=3):
    for i in data[data.isna()].index:
        data[i] = weighted_past_average(data[i - n:i].to_list())
    return data

def identify_windowed_spikes(data, n=14):
    windowed_sum = sum(data[:n])
    spike_indices = []
    for i in range(n, len(data)):
        # Check if you exceed the past window average
        if data[i] > (windowed_sum / n):
            spike_indices.append(i)

        # Adjust the windowed sum to remove the previous and add yourself
        windowed_sum += data[i] - data[i - n]

    return spike_indices

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

# Converts a string year-month-day into a date object
def str_to_date(string):
    pieces = string.split('-')
    return date(int(pieces[0]), int(pieces[1]), int(pieces[2]))

def phase_from_date(phases, date):
    return phases[date.strftime('%Y-%m-%d')]

# Loads date, minHR, and BBT
def load_raw_data():
    data = pd.read_csv("raw_data/sleep_2024-03-22_2025-09-16.csv")
    dates = data['day'].apply(str_to_date).to_list()
    minHeartRateData = remove_nan(data['lowest_heart_rate']).to_list()
    data = data['readiness']

    tempData = []
    for entry in data:
        try:
            if isinstance(entry, str):
                temp = ast.literal_eval(entry)['temperature_deviation']
                if temp:
                    tempData.append(ast.literal_eval(entry)['temperature_deviation'])
                else:
                    # Append the weighted average of the past 3 days to account for missing data
                    tempData.append(weighted_past_average(tempData, n=3))
            else:
                # Append the weighted average of the past 3 days to account for missing data
                tempData.append(weighted_past_average(tempData, n=3))
                print("Found non string")
        except:
            print("uh oh")
    
    return dates, tempData, minHeartRateData

def load_processed_data():
    # Load data
    dates, tempData, minHeartRateData = load_raw_data()
    truthMapping = load_truth_map()

    # Compute label aligned with date
    labels = []
    for date in dates:
        try:
            labels.append(truthMapping[date])
        except:
            print(f"Missing {date}")
            labels.append("missing")

    return tempData, minHeartRateData, labels

def load_truth_map():
    # Load the truth values and produce a mapping from date to annotation
    truth_data = pd.read_csv("calendar_data_full_annotated.csv")
    truthMapping = {}

    for date, label in zip(truth_data['day'], truth_data['phase']):
        truthMapping[str_to_date(date)] = label

    return truthMapping

def compute_accuracy(labels: list, luteal_preds: set, warmup_period=0):
    total_correct = 0
    total_missing = 0

    for i in range(warmup_period, len(labels)):
        if labels[i] == 'missing':
            total_missing += 1
        elif labels[i] == 'luteal' or labels[i] == 'ovulations':
            if i in luteal_preds:
                total_correct += 1
        elif not(i in luteal_preds): # Not in preds means correct pred follicular
            total_correct += 1

    print(f"Out of {len(labels)} labels, {total_missing} are missing")
    return total_correct / (len(labels) - total_missing - warmup_period), total_correct, (len(labels) - total_missing - warmup_period)

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

def compute_confusion_matrix(true_labels: set, pred_labels: set, total_data_size):
    trueNegative, truePositive, falsePositive, falseNegative = [], [], [], []
    streamedMatrix = [] # A stream of TN, TP, FP, FN values
    for i in range(total_data_size):
        if i in true_labels: # truePositive or falsenegative
            if i in pred_labels:
                truePositive.append(i)
                streamedMatrix.append('TP')
            else:
                falseNegative.append(i)
                streamedMatrix.append('FN')
        else: # true negative or false positive
            if i in pred_labels:
                falsePositive.append(i)
                streamedMatrix.append('FP')
            else:
                trueNegative.append(i)
                streamedMatrix.append('TN')

    return trueNegative, truePositive, falsePositive, falseNegative, streamedMatrix

def compute_spiked_prediction_accuracy(data, labels, window_size=14, visualize=True):
    # Smooth data for predictions
    smoothed_data = low_pass(data, window_size=3)

    # Generate predictions from data, classify spikes as luteal phase
    spike_indices = identify_windowed_spikes(smoothed_data, n=window_size)

    # Compute accuracy
    accuracy, total_correct, total_considered = compute_accuracy(labels, set(spike_indices), warmup_period=window_size)
    print(f"Accuracy is f{accuracy}")

    # Visualize predictions versus truth
    if visualize:
        true_spikes = []
        for i in range(window_size, len(labels)):
            if labels[i] == 'luteal' or labels[i] == 'ovulation':
                true_spikes.append(i)

        graph_stacked_with_highlights(smoothed_data, spike_indices, smoothed_data, true_spikes, data0Name='preds', data1Name='true_label')

    # Extract confusion matrix metrics
    # trueNegative, truePositive, falsePositive, falseNegative, streamedMatrix = compute_confusion_matrix(set(true_spikes), temp_spike_indices, total_data_size=len(labels))

    return accuracy, total_correct, total_considered

def main():
    # Load data
    tempData, minHeartRateData, labels = load_processed_data()
    accuracy, total_correct, total_considered = compute_spiked_prediction_accuracy(tempData, labels, visualize=True)
    breakpoint()

if __name__ == '__main__':
    main()