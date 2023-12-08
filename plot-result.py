import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np
import re

def list_csv_files(directory):
    return [file for file in os.listdir(directory) if file.endswith('.csv') and os.path.isfile(os.path.join(directory, file))]

def plot_average_latency(result_directory, pattern, plotname):
    # Compile the regular expression pattern for filenames
    pattern_re = re.compile(pattern)
    
    # Lists to store the indices (x) and the average latencies (y)
    indices = []
    average_latencies = []

    # Sort files to ensure the order is correct
    sorted_files = sorted(filter(pattern_re.match, os.listdir(result_directory)))

    for file_name in sorted_files:
        if '.csv.png' not in file_name:
            # Extract the index from the filename using the compiled pattern
            index = int(pattern_re.match(file_name).group(1))
            file_path = os.path.join(result_directory, file_name)
            
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            
            # Assume the average latency is in the first column after the header
            average_latency = df.iloc[0, 0]
            
            indices.append(index)
            average_latencies.append(average_latency)

    # Plotting the average latencies
    plt.figure(figsize=(12, 6))
    plt.plot(indices, average_latencies, marker='o', linestyle='-')
    plt.title('Average Latency vs. Client Number')
    plt.xlabel('Client Number')
    plt.ylabel('Average Latency')
    plt.grid(True)
    plt.xticks(indices)
    plt.savefig(os.path.join(result_directory, f'{plotname}.png'))

def plotGraph(result_directory):
    csv_files = list_csv_files(result_directory)
    # Loop through each file and create a bar chart for each column
    for file in csv_files:
        file_path = os.path.join(result_directory, file)
        df = pd.read_csv(file_path)

        plt.figure(figsize=(12, 6))
        
        # Plotting bars for each column
        for i, col in enumerate(df.columns):
            # Calculate the mean, max, and min of each column
            mean_value = df[col].mean()
            max_value = df[col].max()
            min_value = df[col].min()

            # Plot the mean value
            plt.bar(col, mean_value, label=f'{col} (mean)')

            # Show max and min values as horizontal lines
            plt.hlines(max_value, xmin=i-0.4, xmax=i+0.4, colors='red', label=f'{col} (max)' if i == 0 else "")
            plt.hlines(min_value, xmin=i-0.4, xmax=i+0.4, colors='green', label=f'{col} (min)' if i == 0 else "")

        plt.title(f'Bar Chart for {file}')
        plt.xlabel('Column')
        plt.ylabel('Value')
        ##plt.legend()
        #plt.legend()
        plt.savefig(os.path.join(result_directory, f'{file}.png'))

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     folder_path = sys.argv[1]
    # else:
    #     print("The folder path is needed as parameter")
    #     exit(1)
    plot_average_latency("test_2023-12-08_23-07-00", "combined_([0-9]+)_epics_results.csv", "combined-epics")
    plot_average_latency("test_2023-12-08_23-07-00", "standalone_([0-9]+)_epics_results.csv", "standalone-epics")
    plotGraph("test_2023-12-08_23-07-00")