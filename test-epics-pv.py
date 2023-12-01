import yaml
from epics import PV
import time
from tqdm import tqdm
import csv
from functools import partial
import datetime

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
    

def test_epix(config):
    number_of_client = 1
    run_for_sec = 10
    if 'pv-to-test' not in config:
        print('No pv configured')
    if 'number-of-client' in config:
        number_of_client = config['number-of-client']
    if 'test-duration' in config:
        run_for_sec = config['test-duration']
    pv_list = config['pv-to-test']
    # create output file for all the pv
    for client_idx in range(number_of_client):
        for pv in pv_list:
            pv_idx_name = "{}_{}".format(pv, client_idx)
            out_file_dict[pv_idx_name] = open("{}_epics.csv".format(pv_idx_name), "w")

            callback_with_index = partial(monitor_handler, pv_idx_name)
            epics_pv[pv_idx_name] = PV(pv, callback=callback_with_index)
    
    interval = 1   # Update interval in seconds
    for _ in tqdm(range(run_for_sec), desc="Progress", unit="s", ncols=100):
        time.sleep(interval)
    #stop all pv and close file
    test_results = {}
    current_datetime = datetime.datetime.now()
    datetime_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    with open(f'{datetime_str}_epics_results.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        # Writing the header (test names)
        for client_idx in range(number_of_client):
            for pv in pv_list:
                    pv_idx_name = "{}_{}".format(pv, client_idx)
                    epics_pv[pv_idx_name].clear_callbacks()
                    out_file_dict[pv_idx_name].close()
                    values = read_data_from_file("{}_{}_epics.csv".format(pv, client_idx))
                    test_results[pv_idx_name] = calculate_average(values)
        writer.writerow(test_results.keys())
        writer.writerow(test_results.values())



def read_data_from_file(file_path):
    """Read nanosecond values from a file and return them as a list of integers."""
    with open(file_path, 'r') as file:
        return [int(line.strip()) for line in file if line.strip()]

def calculate_average(values):
    """Calculate the average of a list of values."""
    return sum(values) / len(values) if values else 0

if __name__ == "__main__":
    config = None
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    test_epix(config)