import pandas as pd
from data_processing_utils import remove_nan, str_to_date, weighted_past_average
import ast

# Loads date, minHR, and BBT
def load_raw_data():
    data = pd.read_csv("../raw_data/sleep_2024-03-22_2025-09-16.csv")
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
    truth_data = pd.read_csv("../calendar_data_full_annotated.csv")
    truthMapping = {}

    for date, label in zip(truth_data['day'], truth_data['phase']):
        truthMapping[str_to_date(date)] = label

    return truthMapping