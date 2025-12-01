


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
