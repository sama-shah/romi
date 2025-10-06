import pandas as pd

def main():
    data = pd.read_csv("calendar_data_full.csv")

    prev = 'luteal'

    for i in range(len(data)):
        if data['phase'][i] == 'fertile':
            data['phase'][i] = 'no_phase'

        if data['phase'][i] == 'no_phase':
            if prev == 'ovulation' or prev == 'luteal':
                data['phase'][i] = 'luteal'
            elif prev == 'period' or prev == 'follicular':
                data['phase'][i] = 'follicular'
            else:
                raise Exception(f"Unknown previous phase {prev} at index {i}")
        
        prev = data['phase'][i]


    breakpoint()


    data.to_csv("calendar_data_full_annotated.csv")


if __name__ == '__main__':
    main()