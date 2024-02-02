import os
import numpy as np
import yaml
from epics import PV
import time
import csv
from functools import partial
import datetime
import sys
import pandas as pd
import k2eg
import logging

sample_file = None
total_bytes_received = 0
start_time_nanoseconds = time.time_ns()
bandwidth_bytes_per_second = 0

def monitor_handler(pv_name, pv_data):
    global sample_file, total_bytes_received, start_time_nanoseconds, bandwidth_bytes_per_second

    current_time_nanoseconds = time.time_ns()
    timestamp = pv_data['timeStamp']
    seconds, nanoseconds = timestamp['secondsPastEpoch'], timestamp['nanoseconds']
    pv_timestamp_nanoseconds = int(seconds * 1e9) + nanoseconds

    latency_nanoseconds = max(current_time_nanoseconds - pv_timestamp_nanoseconds, 0)
    value_size_bytes = calculate_data_size(pv_data['value'])
    total_bytes_received += value_size_bytes

    elapsed_time_seconds = (current_time_nanoseconds - start_time_nanoseconds) / 1e9

    # Check if one second has elapsed since the last reset or if elapsed time is very small
    if elapsed_time_seconds >= 1:
        # Reset start time and total bytes received for the new one-second interval
        logging.info(f"Latency: {latency_nanoseconds}, Bandwidth: {bandwidth_bytes_per_second}")
        start_time_nanoseconds = current_time_nanoseconds
        bandwidth_bytes_per_second = total_bytes_received
        total_bytes_received = 0

    # Write latency and bandwidth to file
    sample_file.write(f"{latency_nanoseconds},{bandwidth_bytes_per_second}\n")
    sample_file.flush()
    
def calculate_data_size(value):
    t = type(value)
    if isinstance(value, (int, float)):
        # Basic numeric types (int, float)
        return sys.getsizeof(value)
    elif isinstance(value, str):
        # String type
        return len(value)  # Number of characters in the string
    elif isinstance(value, (list, tuple)):
        # List or tuple (e.g., array of values)
        return sum(calculate_data_size(item) for item in value)
    elif isinstance(value, dict):
        # Dictionary type (e.g., structured data)
        size = sum(sys.getsizeof(key) + calculate_data_size(val) for key, val in value.items())
        return size + sys.getsizeof(value)
    elif isinstance(value, bytes):
        # Byte array
        return len(value)
    elif value is None:
        # NoneType
        return 0
    else:
        # Fallback for other types
        return sys.getsizeof(value)

def test_k2eg(k: k2eg, config, test_directory, test_prefix, client_total, client_idx, test_name):
    global sample_file
    interval = 1   # Update interval in seconds
    number_of_client = 1
    run_for_sec = 10
    if 'pv-to-test' not in config:
        exit(1)
    if 'test-duration' not in config:
         exit(1)
    if 'pv-protocol' not in config:
         exit(1)
    run_for_sec = config['test-duration']
    pv = config['pv-protocol']+'://'+config['pv-to-test']

    total_time_last = 0
    sample_file = open(os.path.join(test_directory, f'{test_prefix}_{test_name}_{client_total}_{client_idx}_k2eg.sample'), "w")
    k.monitor_many([pv], monitor_handler, 5.0)
    print(run_for_sec, flush=True)
    for i in range(1, run_for_sec + 1):
        time.sleep(1)
        print(i, flush=True)
    k.stop_monitor(config['pv-to-test'])
    sample_file.close()

if __name__ == "__main__":
    k = None
    config = None
    test_directory = 'no-specified-directory'
    test_prefix = 'no-specified-prefix'
    client_total = 0
    client_idx = 0
    if len(sys.argv) > 1:
        # sys.argv[1] will be the first parameter, sys.argv[2] the second, and so on.
        for i, param in enumerate(sys.argv[1:], start=1):
            if i == 1:
                test_directory = param
            elif i ==2:
                test_prefix = param
            elif i ==3:
                client_total = param
            elif i ==4:
                client_idx = param
            elif i ==5:
                test_name = param
            elif i ==6:
                app_idx_offset = param
    else:
        exit(1)
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        
    try:
        logging.basicConfig(
            filename=f'k2eg-{client_total}-{client_idx}.log',
            format="[%(levelname)-8s] %(message)s",
            level=logging.INFO,
            filemode='w'
        )
        app_name = f'app-test-{int(app_idx_offset)+int(client_idx)}'
        k = k2eg.dml('lcls', app_name)
        test_k2eg(k, config, test_directory, test_prefix, client_total, client_idx, test_name)
    except k2eg.OperationError as e:
        logging.error(f"Remote error: {e.error} with message: {e.args[0]}")
    except k2eg.OperationTimeout:
        logging.error("Operation timeout")
        pass
    except ValueError as e:
        logging.error("Bad value {}".format(e))
        pass
    except  TimeoutError as e:
        logging.error("Client timeout")
        pass

    finally:
        if k is not None:
            k.close()