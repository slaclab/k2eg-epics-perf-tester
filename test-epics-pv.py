import os
import yaml
from epics import PV
import time
import csv
from functools import partial
import datetime
import sys
import pandas as pd

sample_file = None


def monitor_handler(pvname=None, posixseconds=None, nanoseconds=None, **kwargs):
    global sample_file
    current_time_nanoseconds = time.time_ns()

    # The EPICS timestamp is a combination of posixseconds and nanoseconds
    pv_timestamp_nanoseconds = int(posixseconds * 1e9) + nanoseconds

    # Calculate latency in nanoseconds
    latency_nanoseconds = current_time_nanoseconds - pv_timestamp_nanoseconds

    # Write latency to file
    sample_file.write(str(latency_nanoseconds) + "\n")
    sample_file.flush()

def test_epix(config, test_directory, test_prefix, client_total, client_idx):
    global sample_file
    interval = 1   # Update interval in seconds
    number_of_client = 1
    run_for_sec = 10
    if 'pv-to-test' not in config:
        exit(1)
    if 'test-duration' not in config:
         exit(1)
        
    run_for_sec = config['test-duration']
    pv = config['pv-to-test']

    total_time_last = 0
    sample_file = open(os.path.join(test_directory, f'{test_prefix}_{client_total}_{client_idx}_epics.sample'), "w")
    epics_pv = PV(pv, callback=monitor_handler)

    print(run_for_sec, flush=True)
    for i in range(1, run_for_sec + 1):
        time.sleep(1)
        print(i, flush=True)

    epics_pv.disconnect()
    sample_file.close()

if __name__ == "__main__":
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
    else:
        exit(1)
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    test_epix(config, test_directory, test_prefix, client_total, client_idx)
    print("completed")