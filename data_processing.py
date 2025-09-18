import pandas as pd
import ast
import matplotlib.pyplot as plt

def low_pass(data, window_size=3):
    newData = []
    
    for i in range(len(data) - window_size):
        newData.append(sum(data[i: i + window_size]) / window_size)

    return newData

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
                    print("Found none type temperature")
            else:
                print("Found non string")
        except:
            print("uh oh")

    smoothed_data = low_pass(tempData, window_size=3)

    plt.plot(smoothed_data)
    plt.show()

if __name__ == '__main__':
    main()