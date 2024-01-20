import os
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


def monitor_handler(pv_name, data):
    # Extract the timestamp data
    timestamp = data['timeStamp']
    seconds_past_epoch = timestamp['secondsPastEpoch']
    nanoseconds = timestamp['nanoseconds']
    
    current_time_nanoseconds = time.time_ns()
    pv_timestamp_nanoseconds = int(seconds_past_epoch * 1e9) + nanoseconds

    # Calculate latency in nanoseconds
    latency_nanoseconds = current_time_nanoseconds - pv_timestamp_nanoseconds

    # Adjust for nanosecond overflow/underflow
    if latency_nanoseconds < 0:
        # Optionally, handle negative latency here (e.g., set to 0, discard, etc.)
        latency_nanoseconds = 0  # Example: Resetting negative latency to 0

    # Write latency to file
    sample_file.write(str(latency_nanoseconds) + "\n")
    sample_file.flush()

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
    else:
        exit(1)
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        
    try:
        logging.basicConfig(
            format="[%(levelname)-8s] %(message)s",
            level=logging.INFO,
        )
        app_name = f'app-test-{client_idx}'
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