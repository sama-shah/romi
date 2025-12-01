
from data_loading import load_processed_data
from menstrual_cycle_prediction import compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy


def main():
    # Load data
    tempData, minHeartRateData, labels, dates = load_processed_data()
    
    accuracy, total_correct, total_considered = compute_weighted_window_period_adjusting_spiked_prediction_with_ovulation_accuracy(tempData, labels, visualize=True)
    breakpoint()

if __name__ == '__main__':
    main()
