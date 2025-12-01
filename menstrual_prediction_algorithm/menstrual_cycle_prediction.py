
from data_processing_utils import low_pass, create_generated_labels
from prediction_primitives import identify_windowed_spikes, identify_weighted_windowed_spikes
from accuracy import compute_accuracy, compute_fertility_accuracy, compute_ovulation_accuracy
from visualize import graph_stacked_with_highlights, display_labels

FERTILE_DAYS_BEFORE_LUTEAL  = 6 # Ends in ovulation day
FERTILE_DAYS_DURING_LUTEAL  = 3 # After ovulation day
PERIOD_LENGTH_DAYS = 5
OUVLATION_FORGIVENESS_WINDOW_DAYS = 3

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
