from datetime import timedelta
from data_loading import load_processed_data


def find_longest_consecutive_day_run(dates):
    """
    Given a list of datetime.date or datetime.datetime objects,
    return (start_index, end_index, run_length) for the longest
    consecutive-day sequence.
    """
    if not dates:
        return -1, -1, 0

    longest_start = 0
    longest_end = 0
    longest_run = 1

    curr_start = 0
    curr_run = 1

    for i in range(1, len(dates)):
        # Check true date continuity using safe timedelta arithmetic
        if dates[i] - dates[i - 1] == timedelta(days=1):
            curr_run += 1
        else:
            # Run ended, evaluate it
            if curr_run > longest_run:
                longest_run = curr_run
                longest_start = curr_start
                longest_end = i - 1

            # Reset for next run
            curr_run = 1
            curr_start = i

    # Handle final run ending at last element
    if curr_run > longest_run:
        longest_run = curr_run
        longest_start = curr_start
        longest_end = len(dates) - 1

    return longest_start, longest_end, longest_run


def main():
    tempData, minHeartRateData, labels, dates = load_processed_data()

    start_idx, end_idx, run_len = find_longest_consecutive_day_run(dates)

    print("Longest consecutive-day run:")
    print(f"  Start index: {start_idx}   ({dates[start_idx]})")
    print(f"  End index:   {end_idx}     ({dates[end_idx]})")
    print(f"  Length:      {run_len} days")


if __name__ == "__main__":
    main()
