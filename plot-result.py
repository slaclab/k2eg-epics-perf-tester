import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
import re

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
            # Assuming latency values are in a column named 'latency'
            average_latency = df.mean()
            print(f'Average for total_clients {clients} and instances {match.group(2)} is {average_latency}')
            # Store data
            if clients in data:
                data[clients].append(average_latency)
            else:
                data[clients] = [average_latency]


    # Calculate overall average for each number of clients
    averages = {k: sum(v)/len(v) for k, v in data.items()}

    # Plotting
    plt.plot(list(averages.keys()), list(averages.values()), marker='o')
    plt.xlabel('Number of Parallel Clients (A)')
    plt.ylabel('Average Latency')
    plt.title('Latency vs. Number of Parallel Clients')
    plt.grid(True)
    plt.savefig(os.path.join(result_directory, f'{plot_name}.png'))

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     folder_path = sys.argv[1]
    # else:
    #     print("The folder path is needed as parameter")
    #     exit(1)
    scan_and_plot("test_2023-12-14_20-29-22", r'sequential_(\d+)_(\d+)_epics.sample', "standalone-epics")
    scan_and_plot("test_2023-12-14_20-29-22", r'sequential_(\d+)_(\d+)_k2eg.sample', "standalone-k2eg")
