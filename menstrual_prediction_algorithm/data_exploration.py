from data_loading import load_processed_data

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


if __name__ == '__main__':
    main()
