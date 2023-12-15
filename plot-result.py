import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import os
import numpy as np
import re
from collections import OrderedDict

def scan_and_plot(result_directory, regex, plot_name):
    # Dictionary to store data
    data = {}

    # Scan for files
    for filename in os.listdir(result_directory):
        match = re.match(regex, filename)
        if match:
            clients = int(match.group(1))
            # Read the file (assuming CSV format with a header)
            df = pd.read_csv(os.path.join(result_directory, filename), header=None)
            if len(df.columns) == 1:
                df = df.iloc[:, 0]
            
            # Convert nanoseconds to milliseconds
            df = df / 1_000_000

            # sort the data
            df_sorted = df.sort_values()
            if len(df_sorted) > 4:
                # Exclude the first two (lowest) and last two (highest) measurements
                df_filtered = df_sorted.iloc[2:-2]
            else:
                # If four or fewer measurements, retain the original data
                df_filtered = df_sorted
            # Assuming latency values are in a column named 'latency'
            average_latency = df_filtered.mean()
            print(f'For {filename} max:{df_filtered.iloc[-1]} min:{df_filtered.iloc[0]} average:{average_latency}')
            # Store data
            if clients in data:
                data[clients].append(average_latency)
            else:
                data[clients] = [average_latency]


    # Calculate overall average for each number of clients
    averages = {k: sum(v)/len(v) for k, v in data.items()}
    # Sorting the dictionary by its keys
    averages = OrderedDict(sorted(averages.items(), key=lambda item: int(item[0])))


    # Plotting
    plt.clf()
    plt.plot(list(averages.keys()), list(averages.values()), marker='o')
    plt.xlabel('Number of Parallel Clients (A)')
    plt.ylabel('Average Latency')
    plt.title(f'{plot_name}: Latency vs. Number of Parallel Clients')
    plt.grid(True)
    # Set x-axis to only use integer values
    ax = plt.gca()  # Get the current axis
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.savefig(os.path.join(result_directory, f'{plot_name}.png'))

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     folder_path = sys.argv[1]
    # else:
    #     print("The folder path is needed as parameter")
    #     exit(1)
    scan_and_plot("test_2023-12-15_22-03-51", r'sequential_(\d+)_(\d+)_epics.sample', "standalone-epics")
    scan_and_plot("test_2023-12-15_22-03-51", r'sequential_(\d+)_(\d+)_k2eg.sample', "standalone-k2eg")
