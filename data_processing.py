import pandas as pd
import ast
import matplotlib.pyplot as plt
from datetime import date

FOLLICULAR = 0
LUTEAL = 1
MENSES = 2
OVULATION = 3

FERTILE_DAYS_BEFORE_LUTEAL  = 6 # Ends in ovulation day
FERTILE_DAYS_DURING_LUTEAL  = 3 # After ovulation day
PERIOD_LENGTH_DAYS = 5
OUVLATION_FORGIVENESS_WINDOW_DAYS = 3

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

def identify_weighted_windowed_spikes(data, n=14):
    windowed_sum = sum(data[:n])
    spike_indices = []
    current_run_size = n # Tracking the length of the current run
                         # Used to incentize runs around the window length
    spiked_run = False

    for i in range(n, len(data)):
        # Percentage of the elapsed target window
        # TODO: instead of linear scaling of weight, experiment with harmonic or exponential
        run_weight = current_run_size / n

        # If in a spiked run, invert run weight to lower the threshold to stop the run
        if spiked_run:
            run_weight = run_weight
        else:
            run_weight = 2 - run_weight

        # Debug
        # print(f"Spiked_run={spiked_run}, current_run_size={current_run_size}, run_weight={run_weight}")
        # print(f"Comparing data={data[i]} with {(run_weight * (windowed_sum / n))}")

        # Check if you exceed the past window average
        if data[i] > (run_weight * (windowed_sum / n)):
            if not spiked_run:
                spiked_run = True
                current_run_size = 0
            spike_indices.append(i)
        elif spiked_run:
            spiked_run = False
            current_run_size = 0

        # Adjust the windowed sum to remove the previous and add yourself
        windowed_sum += data[i] - data[i - n]

        current_run_size += 1

    return spike_indices

# def period_adjusting_identify_weighted_windowed_spikes(data, labels, n=14):
#     windowed_sum = sum(data[:n])
#     spike_indices = []
#     spiked_run = False
    
#     # Estimate run size from the first windows days of data
#     if 'period' in labels[:n]:
#         current_run_size = n - labels.index('period')
#     else:
#         current_run_size = n # Tracking the length of the current run
#                         # Used to incentize runs around the window length

#     for i in range(n, len(data)):
#         # Percentage of the elapsed target window
#         # TODO: instead of linear scaling of weight, experiment with harmonic or exponential
#         run_weight = current_run_size / n

#         # If in a spiked run, invert run weight to lower the threshold to stop the run
#         if spiked_run:
#             run_weight = run_weight
#         else:
#             run_weight = 2 - run_weight

#         # Debug
#         # print(f"Spiked_run={spiked_run}, current_run_size={current_run_size}, run_weight={run_weight}")
#         # print(f"Comparing data={data[i]} with {(run_weight * (windowed_sum / n))}")

#         # Check if you exceed the past window average
#         if data[i] > (run_weight * (windowed_sum / n)):
#             if not spiked_run:
#                 spiked_run = True
#                 current_run_size = 0
#             spike_indices.append(i)
#         elif spiked_run:
#             spiked_run = False
#             current_run_size = 0

#         # Adjust the windowed sum to remove the previous and add yourself
#         windowed_sum += data[i] - data[i - n]

#         current_run_size += 1

#         # Recalibrate if you recieve a reported period which you didn't account for
#         # if labels[i-1] != 'period' and labels[i] == 'period' or  and spiked_run:
#         if labels[i-1] != 'period' and labels[i] == 'period':
#             current_run_size = 1
#             spiked_run = False

#     return spike_indices

def period_adjusting_identify_weighted_windowed_spikes(data, labels, n=14):
    windowed_sum = sum(data[:n])
    spike_indices = []
    ovulation_indices = []
    fertility_indices = []
    period_indices = []
    spiked_run = False
    
    # Estimate run size from the first windows days of data
    if 'period' in labels[:n]:
        current_run_size = n - labels.index('period')
    else:
        current_run_size = n # Tracking the length of the current run
                        # Used to incentize runs around the window length

    for i in range(n, len(data)):
        if current_run_size == (n - FERTILE_DAYS_BEFORE_LUTEAL) and not spiked_run:
            for j in range(FERTILE_DAYS_BEFORE_LUTEAL + FERTILE_DAYS_DURING_LUTEAL):
                fertility_indices.append(j + i)
            ovulation_indices.append(i + FERTILE_DAYS_BEFORE_LUTEAL)
        run_weight = current_run_size / n

        # If in a spiked run, invert run weight to lower the threshold to stop the run
        if spiked_run:
            run_weight = run_weight
        else:
            run_weight = 2 - run_weight

        # Debug
        # print(f"Spiked_run={spiked_run}, current_run_size={current_run_size}, run_weight={run_weight}")
        # print(f"Comparing data={data[i]} with {(run_weight * (windowed_sum / n))}")

        # Check if you exceed the past window average
        if data[i] > (run_weight * (windowed_sum / n)):
            if not spiked_run:
                spiked_run = True
                current_run_size = 0
            spike_indices.append(i)
        elif spiked_run:
            spiked_run = False
            for j in range(PERIOD_LENGTH_DAYS):
                period_indices.append(i + j)
            current_run_size = 0

        # Adjust the windowed sum to remove the previous and add yourself
        windowed_sum += data[i] - data[i - n]

        current_run_size += 1

        # Recalibrate if you recieve a reported period which you didn't account for
        # if labels[i-1] != 'period' and labels[i] == 'period' or  and spiked_run:
        if labels[i-1] != 'period' and labels[i] == 'period':
            current_run_size = 1
            spiked_run = False
    # breakpoint() 
    return ovulation_indices, fertility_indices, spike_indices, period_indices

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

    return tempData, minHeartRateData, labels, dates

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
        elif labels[i] == 'luteal' or labels[i] == 'ovulation':
            if i in luteal_preds:
                total_correct += 1
        elif not(i in luteal_preds): # Not in preds means correct pred follicular
            total_correct += 1

    print(f"Out of {len(labels)} labels, {total_missing} are missing")
    return total_correct / (len(labels) - total_missing - warmup_period), total_correct, (len(labels) - total_missing - warmup_period)

def compute_ovulation_accuracy(labels: list, ovulation_preds: set, warmup_period=0):
    total_correct = 0
    total_missing = 0

    for i in ovulation_preds:
        # Go over all values in the window and check if any of them are ovulation
        for j in range(i - OUVLATION_FORGIVENESS_WINDOW_DAYS, i + OUVLATION_FORGIVENESS_WINDOW_DAYS + 1):
            if labels[j] == 'ovulation':
                total_correct += 1
                break
        
    total_considered = labels[warmup_period:].count('ovulation')
    
    return total_correct / total_considered, total_correct, total_considered

def compute_fertility_accuracy(labels: list, fertility_preds: set, warmup_period=0):
    total_correct = 0
    total_missing = 0

    for i in fertility_preds:
        if labels[i] == 'ovulation' or labels[i] == 'fertile':
           total_correct += 1
        
    total_considered = labels[warmup_period:].count('ovulation') + labels[warmup_period:].count('fertile')

    return total_correct / total_considered, total_correct, total_considered


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

def compute_weighted_window_spiked_prediction_accuracy(data, labels, window_size=14, visualize=True):
    # Smooth data for predictions
    smoothed_data = low_pass(data, window_size=3)

    # Generate predictions from data, classify spikes as luteal phase
    spike_indices = identify_weighted_windowed_spikes(smoothed_data, n=window_size)

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

    return accuracy, total_correct, total_considered 

def compute_weighted_window_period_adjusting_spiked_prediction_accuracy(data, labels, window_size=14, visualize=True):
    # Smooth data for predictions
    smoothed_data = low_pass(data, window_size=3)

    # Generate predictions from data, classify spikes as luteal phase
    spike_indices = period_adjusting_identify_weighted_windowed_spikes(smoothed_data, labels, n=window_size)

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

    return accuracy, total_correct, total_considered 

# Creates labeled data from generated labels
def create_generated_labels(num_data_points, ovulation_indices, fertility_indices, spike_indices, period_indices):
    generated_labels = []
    for i in range(num_data_points):
        if i in ovulation_indices:
            generated_labels.append('ovulation')
        elif i in fertility_indices: 
            generated_labels.append('fertile')
        elif i in spike_indices:
            generated_labels.append('luteal')
        elif i in period_indices:
            generated_labels.append('period')
        else:
            generated_labels.append('follicular')
    return generated_labels

def display_labels(true_labels, generated_labels, starting_day):
    col_width = 15
    print("\t Expected   Predicted")
    for i, (true_label, generated) in enumerate(zip(true_labels, generated_labels)):
        if(i >= starting_day):
            print(f"Day {i}: {true_label:<{col_width}} {generated}")

def compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy(data, labels, window_size=14, visualize=True):
    # Smooth data for predictions
    smoothed_data = low_pass(data, window_size=3)

    # Generate predictions from data, classify spikes as luteal phase
    ovulation_indices, fertility_indices, spike_indices, period_indices = period_adjusting_identify_weighted_windowed_spikes(smoothed_data, labels, n=window_size)

    # Compute ovulation distances
    ovulation_distances = []
    ovulation_true_indices = [i for i, x in enumerate(labels) if x == 'ovulation']
    for i in range(len(ovulation_indices)):
        min_distance = 100000
        for j in range(len(ovulation_true_indices)):
            if abs(ovulation_true_indices[j] - ovulation_indices[i]) < min_distance:
                min_distance = abs(ovulation_true_indices[j] - ovulation_indices[i])
        ovulation_distances.append(min_distance)

    generated_labels = create_generated_labels(len(labels), ovulation_indices, fertility_indices, spike_indices, period_indices)
    display_labels(labels, generated_labels, window_size)
    # 198-219 is fishy, no period - because of a 1 week gap in the data which causes misalignment
    # dates[211] = 12/2 and dates[212] = 12/9
    match, total = 0, 0
    for i, (truth, generated) in enumerate(zip(labels[window_size:198], generated_labels[window_size:198])):
        total += 1
        if (truth == generated) or (truth == 'period' and generated == 'follicular') or (truth == 'follicular' and generated == 'period'):
            match += 1
        else:
            print(f"Day {i} mismatch: {truth} {generated}")
    print(f"{match} matches on the range of {total} for accuracy of {match/total}")


    # Compute accuracy
    luteal_accuracy, luteal_total_correct, luteal_total_considered = compute_accuracy(labels, set(spike_indices), warmup_period=window_size)
    ovulation_accuracy, ovulation_total_correct, ovulation_total_considered = compute_ovulation_accuracy(labels, set(ovulation_indices[:7]), warmup_period=window_size)
    fertility_accuracy, fertility_total_correct, fertility_total_considered = compute_fertility_accuracy(labels, set(fertility_indices), warmup_period=window_size)
    print(f"Luteal accuracy is f{luteal_accuracy}")
    print(f"Ovulation accuracy is f{ovulation_accuracy}")
    print(f"Fertility accuracy is f{fertility_accuracy}")
    breakpoint()

    # Visualize predictions versus truth
    if visualize:
        true_spikes = []
        for i in range(window_size, len(labels)):
            if labels[i] == 'luteal' or labels[i] == 'ovulation':
                true_spikes.append(i)

        graph_stacked_with_highlights(smoothed_data, spike_indices, smoothed_data, true_spikes, data0Name='preds', data1Name='true_label')

    return luteal_accuracy, luteal_total_correct, luteal_total_considered 

def main():
    # Load data
    tempData, minHeartRateData, labels, dates = load_processed_data()
    

    longestRun = -1
    longestStart = -1
    longestEnd = -1
    currRun = 0
    start = -1
    end = -1

    for i in range(1, len(dates)):
        print(dates[i], currRun)
        if(dates[i].day == (dates[i-1].day + 1) or (dates[i].day == 1 and (dates[i].month) == ((dates[i-1].month + 1) % 12))):
            if currRun == 0:
                start = i
            currRun += 1
        else:
            end = i
            if currRun > longestRun:
                longestStart = start
                longestEnd = end
                longestRun = currRun
            currRun = 0
    if currRun > longestRun:
        longestStart = start
        longestEnd = end
        longestRun = currRun

    # accuracy, total_correct, total_considered = compute_weighted_window_spiked_prediction_accuracy(tempData, labels, visualize=True)
    accuracy, total_correct, total_considered = compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy(tempData, labels, visualize=True)
    breakpoint()

if __name__ == '__main__':
    main()