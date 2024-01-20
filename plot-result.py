import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import os
import numpy as np
import re
from collections import OrderedDict
import sys

def scan_and_plot(result_directory, regex, plot_name):
    # Dictionary to store data
    data = {}

    # Scan for files
    for filename in os.listdir(result_directory):
        match = re.match(regex, filename)
        if match:
            test_name = match.group(1)
            clients = int(match.group(2))

            # Read the file (assuming CSV format with a header)
            df = pd.read_csv(os.path.join(result_directory, filename), header=None)
            if len(df.columns) == 1:
                df = df.iloc[:, 0]

            # Convert nanoseconds to milliseconds
            df = df / 1_000_000

            # Sort the data
            df_sorted = df.sort_values()
            if len(df_sorted) > 4:
                # Exclude the first two (lowest) and last two (highest) measurements
                df_filtered = df_sorted.iloc[2:-2]
            else:
                # If four or fewer measurements, retain the original data
                df_filtered = df_sorted

            # Assuming latency values are in a column named 'latency'
            average_latency = df_filtered.mean()

            # Store data
            key = (test_name, clients)
            if key in data:
                data[key].append(average_latency)
            else:
                data[key] = [average_latency]

    # Get unique test names and sort them
    test_names = sorted(set(k[0] for k in data.keys()))

    # Create subplots
    fig, axs = plt.subplots(len(test_names), 1, figsize=(10, 5 * len(test_names)))

    # Check if axs is a single Axes object (happens when len(test_names) is 1)
    if len(test_names) == 1:
        axs = [axs]

    for ax, test_name in zip(axs, test_names):
        test_data = {k[1]: v for k, v in data.items() if k[0] == test_name}
        # Calculate overall average for each test name and number of clients
        averages = {k: sum(v)/len(v) for k, v in test_data.items()}
        # Sorting the dictionary by its keys
        averages = OrderedDict(sorted(averages.items(), key=lambda item: int(item[0])))

        # Plotting
        ax.plot(list(averages.keys()), list(averages.values()), marker='o', label=test_name)
        ax.set_xlabel('Number of Parallel Clients (A)')
        ax.set_ylabel('Average Latency')
        ax.set_title(f'{test_name}: Latency vs. Number of Parallel Clients')
        ax.legend()
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()
    plt.savefig(os.path.join(result_directory, f'{plot_name}.png'))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        print("The folder path is needed as parameter")
        exit(1)
    scan_and_plot(folder_path, r'sequential_(\w+)_(\d+)_(\d+)_epics.sample', "standalone-epics")
    scan_and_plot(folder_path, r'sequential_(\w+)_(\d+)_(\d+)_k2eg.sample', "standalone-k2eg")