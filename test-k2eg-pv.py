import os
import yaml
from epics import PV
import time
import csv
from functools import partial
import datetime
import sys

out_file_dict = {}
epics_pv = {}

def monitor_handler(pv_index_name, pvname=None, data=None, timestamp=None, **kwargs):
    current_time_nanoseconds = time.time_ns()

    # Convert the PV timestamp to nanoseconds
    pv_timestamp_nanoseconds = int(timestamp * 1e9)

    # Calculate latency in seconds and nanoseconds
    latency_nanoseconds = current_time_nanoseconds - pv_timestamp_nanoseconds

    # Adjust for nanosecond overflow/underflow
    if latency_nanoseconds < 0:
        latency_nanoseconds += 1e9

    #print(f"PV:{pvname} latency  nanousec:{latency_nanoseconds}")
    out_file_dict[pv_index_name].write(str(latency_nanoseconds) + "\n")
    out_file_dict[pv_index_name].flush()
    

def test_epix(config, test_directory, test_prefix):
    interval = 1   # Update interval in seconds
    number_of_client = 1
    run_for_sec = 10
    if 'pv-to-test' not in config:
        print('No pv configured')
    if 'number-of-client' in config:
        number_of_client = config['number-of-client']
    if 'test-duration' in config:
        run_for_sec = config['test-duration']
    pv_list = config['pv-to-test']


    # send the total number of second of test each test last for 'run_for_sec' 
    # second and will be reaped for a 'number_of_client' times
    print(run_for_sec*number_of_client, flush=True)
    total_time_last = 0
    for current_client_count in range(1, number_of_client + 1):
        result_file_name = f'{test_prefix}_{current_client_count}_k2eg_results.csv'
        full_result_path = os.path.join(test_directory, result_file_name)
        # Setup and subscribe to PVs for the current number of clients
        for client_idx in range(current_client_count):
            for pv in pv_list:
                pv_idx_name = f"{pv}_{client_idx}"
                out_file_dict[pv_idx_name] = open(os.path.join(test_directory, f"{pv_idx_name}_{current_client_count}_k2eg.sample"), "w")
                callback_with_index = partial(monitor_handler, pv_idx_name)
                epics_pv[pv_idx_name] = PV(pv, callback=callback_with_index)
    
        # wait for completion of the single test
        for i in range(1, run_for_sec + 1):
            total_time_last = total_time_last +1
            print(total_time_last, flush=True)
            time.sleep(interval)
        #stop all pv and close file
        test_results = {}
        with open(full_result_path, 'w', newline='') as file:
            writer = csv.writer(file)
            # Writing the header (test names)
            for client_idx in range(current_client_count):
                for pv in pv_list:
                        pv_idx_name = "{}_{}".format(pv, client_idx)
                        epics_pv[pv_idx_name].clear_callbacks()
                        out_file_dict[pv_idx_name].close()
                        csv_file = os.path.join(test_directory, f"{pv}_{client_idx}_{current_client_count}_k2eg.sample")
                        values = read_data_from_file(csv_file)
                        #os.remove(csv_file)
                        test_results[pv_idx_name] = calculate_average(values)
            writer.writerow(test_results.keys())
            writer.writerow(test_results.values())

def read_data_from_file(file_path):
    """Read nanosecond values from a file and return them as a list of integers."""
    with open(file_path, 'r') as file:
        data = [float(line.strip()) for line in file if line.strip()]
    
        # Ensure that there are enough data points to remove two values
    if len(data) > 2:
        data.sort()
        return data[1:-1]  # Exclude the first and last elements (lowest and highest)
    else:
        return data  # Return the data as-is if there aren't enough elements to remove two


def calculate_average(values):
    """Calculate the average of a list of values."""
    return sum(values) / len(values) if values else 0

if __name__ == "__main__":
    config = None
    test_directory = 'no-specified-directory'
    test_prefix = 'no-specified-prefix'
    if len(sys.argv) > 1:
        # sys.argv[1] will be the first parameter, sys.argv[2] the second, and so on.
        for i, param in enumerate(sys.argv[1:], start=1):
            if i == 1:
                test_directory = param
            elif i ==2:
                test_prefix = param
    else:
        exit(1)
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    test_epix(config, test_directory, test_prefix)
    print("completed")