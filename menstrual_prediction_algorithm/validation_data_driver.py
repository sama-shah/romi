import pandas as pd
import ast
import matplotlib.pyplot as plt
from datetime import date

from data_processing_utils import compute_spiked_prediction_accuracy, compute_weighted_window_spiked_prediction_accuracy, compute_weighted_window_period_adjusting_spiked_prediction_accuracy

# Parse data per participant (each is a dictionary of lists)
def load_processed_data(
        filepath, 
        tempDataPerParticipant={}, 
        minHeartRatePerParticipant={}, 
        labelsPerParticipant={}
    ):
    data = pd.read_csv(filepath)
    # tempDataPerParticipant, minHeartRatePerParticipant, labelsPerParticipant = {}, {}, {}

    allParticipants = set(data['id'].to_list())

    # Replace labels to only have luteal, period, follicular, ovulation
    for participant in allParticipants:
        participant_mask = data['id'] == participant
        tempDataPerParticipant[participant] = data['basal_body_temperature'][participant_mask].to_list()
        minHeartRatePerParticipant[participant] = data['min_heart_rate'][participant_mask].to_list()
        labelsPerParticipant[participant] = data['phase'][participant_mask]
        labelsPerParticipant[participant] = labelsPerParticipant[participant].replace('Luteal', 'luteal')
        labelsPerParticipant[participant] = labelsPerParticipant[participant].replace('Menstrual', 'period')
        labelsPerParticipant[participant] = labelsPerParticipant[participant].replace('Fertility', 'follicular') # For now assume all fertile periods are follicular
        labelsPerParticipant[participant] = labelsPerParticipant[participant].replace('Follicular', 'follicular')
        labelsPerParticipant[participant] = labelsPerParticipant[participant].to_list()

    
    # breakpoint()

    return tempDataPerParticipant, minHeartRatePerParticipant, labelsPerParticipant

def main():
    # Load data
    tempData, minHeartRateData, labels = load_processed_data("validation_data/mcphases_2022.csv")
    tempData, minHeartRateData, labels = load_processed_data("validation_data/mcphases_2024.csv", tempData, minHeartRateData, labels)

    # Debug particpant
    # DEBUG_PARTICIPANT = '22_2024' # Seems to need something to incentivize phases closer to the length, add some hyperparam which shifts the threshold as time passes
    # DEBUG_PARTICIPANT = '32_2022' # Needs something to extend phases and dynamicly recalibrate if mispredict on period day
    # DEBUG_PARTICIPANT = '50_2024' # Needs something to extend phases and dynamicly recalibrate if mispredict on period day
    # DEBUG_PARTICIPANT = '10_2024' # Needs something to account for predicting period, but mispredicting
    # DEBUG_PARTICIPANT = '13_2022' # Needs something to account for predicting period, but mispredicting
    # accuracy, total_correct, total_considered = compute_weighted_window_period_adjusting_spiked_prediction_accuracy(tempData[DEBUG_PARTICIPANT], labels[DEBUG_PARTICIPANT], visualize=True)
    # breakpoint()

    accuracies = []
    breakpoint()
    total_skipped = 0
    for participant in tempData.keys():
        # if 'period' in labels[participant]:
        if True:
            print(f"Participant {participant}: ")
            # Original version - 60.877
            # accuracy, total_correct, total_considered = compute_spiked_prediction_accuracy(tempData[participant], labels[participant], visualize=False)
            
            # Weighted window version (incentizing phases to last as long as the expected window) - 49.079007467234
            # accuracy, total_correct, total_considered = compute_weighted_window_spiked_prediction_accuracy(tempData[participant], labels[participant], visualize=False)
            
            # Period aware, which take into account suprise period during luteal prediction - 73.45439191518064
            accuracy, total_correct, total_considered = compute_weighted_window_period_adjusting_spiked_prediction_accuracy(tempData[participant], labels[participant], visualize=False)
            accuracies.append(accuracy)
            print()
        else:
            total_skipped += 1
            print(f"No menstrual phase in participant {participant}, skipping\n")

    print(f"Average accuracy: {sum(accuracies) / len(accuracies)}")
    print(f"Skipped {total_skipped} participants")
    # accuracy, total_correct, total_considered = compute_spiked_prediction_accuracy(tempData, labels, visualize=True)
    breakpoint()

if __name__ == '__main__':
    main()
