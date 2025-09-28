import pandas as pd
import ast
import matplotlib.pyplot as plt

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

def main():
    data = pd.read_csv("raw_data/sleep_2024-03-22_2025-09-16.csv")
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

    smoothed_data = low_pass(tempData, window_size=3)
    smoothed_data = smoothed_data[:100]
    spike_indices = identify_windowed_spikes(smoothed_data, n=14)

    for spike in spike_indices:
        plt.axvline(x=spike, color='r', linestyle='-', linewidth=2)

    plt.plot(smoothed_data)
    plt.show()

if __name__ == '__main__':
    main()