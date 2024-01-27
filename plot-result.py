import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import os
import numpy as np
import re
from collections import OrderedDict
import sys

def scan_and_plot(result_directory, regex, plot_file_name):
    # Dictionaries to store latency and bandwidth data by plot name
    data = {}

    # Scan for files
    for filename in os.listdir(result_directory):
        match = re.match(regex, filename)
        if match:
            plot_name = match.group(1)
            clients = int(match.group(2))

            # Read the file (assuming CSV format with two columns)
            df = pd.read_csv(os.path.join(result_directory, filename), header=None)

            # Process latency data (first column)
            latency = df.iloc[:, 0] / 1_000_000  # Convert nanoseconds to milliseconds
            latency_sorted = latency.sort_values()
            latency_filtered = latency_sorted.iloc[2:-2] if len(latency_sorted) > 4 else latency_sorted
            average_latency = latency_filtered.mean()

            # Process bandwidth data (second column)
            bandwidth = df.iloc[:, 1]  # Assuming bandwidth is in bytes/second
            bandwidth_sorted = bandwidth.sort_values()
            bandwidth_filtered = bandwidth_sorted.iloc[2:-2] if len(bandwidth_sorted) > 4 else bandwidth_sorted
            average_bandwidth = bandwidth_filtered.mean()

            # Store data by plot name
            if plot_name not in data:
                data[plot_name] = {'latency': {}, 'bandwidth': {}}
            data[plot_name]['latency'].setdefault(clients, []).append(average_latency)
            data[plot_name]['bandwidth'].setdefault(clients, []).append(average_bandwidth)

    # Create subplots for each plot name
    fig, axs = plt.subplots(len(data), 1, figsize=(10, 5 * len(data)))

    # Check if axs is a single Axes object (happens when there is only one plot name)
    if len(data) == 1:
        axs = [axs]

    for ax, (plot_name, metrics) in zip(axs, data.items()):
        # Calculate overall averages
        latency_averages = {k: sum(v)/len(v) for k, v in metrics['latency'].items()}
        bandwidth_averages = {k: sum(v)/len(v) for k, v in metrics['bandwidth'].items()}
        # Sorting the dictionaries by their keys
        latency_averages = OrderedDict(sorted(latency_averages.items(), key=lambda item: int(item[0])))
        bandwidth_averages = OrderedDict(sorted(bandwidth_averages.items(), key=lambda item: int(item[0])))

        # Plot latency on the left y-axis
        ax.plot(list(latency_averages.keys()), list(latency_averages.values()), marker='o', color='b', label='Latency')
        ax.set_xlabel('Number of Parallel Clients (A)')
        ax.set_ylabel('Average Latency (ms)', color='b')
        ax.tick_params(axis='y', labelcolor='b')

        # Create a second y-axis for bandwidth
        ax2 = ax.twinx()
        ax2.plot(list(bandwidth_averages.keys()), list(bandwidth_averages.values()), marker='s', color='r', label='Bandwidth')
        ax2.set_ylabel('Average Bandwidth (bytes/second)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')

        ax.set_title(f'{plot_name}: Latency and Bandwidth vs. Number of Parallel Clients')
        ax.grid(True)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()  # Adjust layout for the secondary y-axis
    plt.savefig(os.path.join(result_directory, f'{plot_file_name}.png'))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        print("The folder path is needed as parameter")
        exit(1)
    scan_and_plot(folder_path, r'sequential_(\w+)_(\d+)_(\d+)_epics.sample', "standalone-epics")
    scan_and_plot(folder_path, r'sequential_(\w+)_(\d+)_(\d+)_k2eg.sample', "standalone-k2eg")