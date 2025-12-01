from datetime import date

# Converts a string year-month-day into a date object
def str_to_date(string):
    pieces = string.split('-')
    return date(int(pieces[0]), int(pieces[1]), int(pieces[2]))

def phase_from_date(phases, date):
    return phases[date.strftime('%Y-%m-%d')]

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

