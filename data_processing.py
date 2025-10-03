import pandas as pd
import ast
import matplotlib.pyplot as plt
from datetime import date

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

def main():
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

    smoothed_temp_data = low_pass(tempData, window_size=3)
    smoothed_hr_data = low_pass(minHeartRateData, window_size=3)
    # plot_curve_pairs(smoothed_temp_data[:200], smoothed_hr_data[:200], 'temp', 'hr')

    PLOT_WINDOW_START = 100
    PLOT_WINDOW_END = 200
    smoothed_temp_data = smoothed_temp_data[PLOT_WINDOW_START:PLOT_WINDOW_END]
    smoothed_hr_data = smoothed_hr_data[PLOT_WINDOW_START:PLOT_WINDOW_END]
    temp_spike_indices = identify_windowed_spikes(smoothed_temp_data, n=14)
    hr_spike_indices = identify_windowed_spikes(smoothed_hr_data, n=14)

    # Graph preds on separate graphs for comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True) 

    # Plot on the first (top) subplot
    ax1.plot(smoothed_temp_data, color='blue')
    ax1.set_title('BBT pred')
    ax1.set_ylabel('temp')

    for spike in temp_spike_indices:
        ax1.axvline(x=spike, color='r', linestyle='-', linewidth=2)

    # Plot on the second (bottom) subplot
    ax2.plot(smoothed_hr_data, color='red')
    ax2.set_title('HR Pred')
    ax2.set_ylabel('hr')

    for spike in hr_spike_indices:
        plt.axvline(x=spike, color='g', linestyle='-', linewidth=2)

    # Adjust layout to prevent labels from overlapping
    plt.tight_layout()

    # Display the plot
    plt.show()

    # plt.plot(smoothed_hr_data[200:300])
    # plt.show()

if __name__ == '__main__':
    main()