import matplotlib.pyplot as plt
import pandas as pd
import os
import numpy as np

def list_csv_files(directory):
    return [file for file in os.listdir(directory) if file.endswith('.csv') and os.path.isfile(os.path.join(directory, file))]

def plotGraph(result_directory):
    csv_files = list_csv_files(result_directory)
    # Loop through each file and create a bar chart for each column
    for file in csv_files:
        file_path = os.path.join(result_directory, file)
        df = pd.read_csv(file_path)

        plt.figure(figsize=(12, 6))
        
        # Number of rows (data points) in the DataFrame
        num_rows = len(df)
        
        # Plotting bars for each column
        for i, col in enumerate(df.columns):
            # Use the mean of each column for the bar height
            mean_value = df[col].mean()
            plt.bar(col, mean_value, label=f'{col} (mean)')

        plt.title(f'Bar Chart for {file}')
        plt.xlabel('Column')
        plt.ylabel('Average Value')
        plt.legend()
        plt.savefig(os.path.join(result_directory, f'{file}.png'))

if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     folder_path = sys.argv[1]
    # else:
    #     print("The folder path is needed as parameter")
    #     exit(1)
    plotGraph("test_2023-12-08_21-21-21")