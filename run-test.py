import os
import subprocess
import concurrent.futures
import threading
import time
import datetime
import sys
import pandas as pd
import matplotlib.pyplot as plt
import yaml

# Global progress state and lock
progress_dict = {}  # To track progress of each script
max_steps_dict = {}  # To track total steps for each script
progress_lock = threading.Lock()

def update_progress_bar(bar_length=50):
    with progress_lock:
        active_tests = [script for script in progress_dict if progress_dict[script] < max_steps_dict[script]]
        total_progress = sum((progress_dict[script] / max_steps_dict[script] for script in active_tests if max_steps_dict[script] > 0))
        total_active_tests = len(active_tests)
        average_progress = (total_progress / total_active_tests) * 100 if total_active_tests > 0 else 100
        filled_length = int(bar_length * average_progress // 100)
        progress_bar = '#' * filled_length + '-' * (bar_length - filled_length)
        print(f"\rProgress: [{progress_bar}] {average_progress:.2f}%", end='', flush=True)
        sys.stdout.flush()  # Explicitly flush the output


def run_test(script, start_test_time, mode, client_total, client_id):
    params = [str(start_test_time), str(mode), str(client_total), str(client_id)]
    with subprocess.Popen(["python", script] + params, stdout=subprocess.PIPE, text=True) as proc:
        first_message = True
        for line in proc.stdout:
            try:
                value = int(line.strip())
                with progress_lock:
                    if first_message:
                        max_steps_dict[script] = value
                        progress_dict[script] = 0
                        first_message = False
                    else:
                        progress_dict[script] = value
                update_progress_bar()
            except ValueError:
                pass
    with progress_lock:
        if script in progress_dict:
            del progress_dict[script]
        if script in max_steps_dict:
            del max_steps_dict[script]

def get_config_value(config, config_key):
    if config_key not in config:
        return None
    else:
        return config[config_key]
    
def execute_scripts(all_script, start_test_time, number_of_clients, mode):
    # Execute the tests with increasing number of parallel clients
    for client_total in range(1, number_of_clients + 1):
        print(f"\nRunning test with {client_total} parallel client(s)")

        # Create a ThreadPoolExecutor with a number of workers equal to client_num
        with concurrent.futures.ThreadPoolExecutor(max_workers=client_total) as executor:
            # Submitting run_test for each script with the current number of clients
            futures = [
                executor.submit(run_test, script, start_test_time, mode, client_total, client_id)
                for client_id in range(1, client_total + 1)
                for script in all_script
            ]

            # Wait for all the futures to complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()  # Get the result of each future
            # You can process the result here

def main():
    config = None
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    if config is None:
        print('No config found!')
        exit(1)
    
    number_of_clients = get_config_value(config, 'number-of-client')
    if number_of_clients is None:
        print('No number of client found found!')
        exit(1)

    #create folder with the start test time
    start_test_time = 'test_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.mkdir(start_test_time) 

    # Running scripts sequentially
    print("Execute sequential tests")
    progress_dict.clear()
    max_steps_dict.clear()
    all_script = [
        "test-epics-pv.py"
    ]
    execute_scripts(all_script, start_test_time, number_of_clients, 'sequential')
    
    # Clear the progress for the new set of tests
    progress_dict.clear()
    max_steps_dict.clear()
    all_script = [
        "test-k2eg-pv.py"
    ]
    execute_scripts(all_script, start_test_time, number_of_clients, 'sequential')

    progress_dict.clear()
    max_steps_dict.clear()
    all_script = [
        "test-epics-pv.py",
        "test-k2eg-pv.py"
    ]
    # Create a ThreadPoolExecutor with a number of workers equal to client_num
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_script)) as executor:
        # Submitting run_test for each script with the current number of clients
        futures = [
            executor.submit(execute_scripts, script, start_test_time, number_of_clients, "paralles") 
            for script in all_script
        ]

        # Wait for all the futures to complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()  # Get the result of each future
            # You can process the result here
    execute_scripts(all_script, number_of_clients, 'parallels')
    print("\ntest compelted!")
if __name__ == "__main__":
    main()