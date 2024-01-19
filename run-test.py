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
import logging
# Global progress state and lock
progress_dict = {}  # To track progress of each script
max_steps_dict = {}  # To track total steps for each script
progress_lock = threading.Lock()
progress_bar_positions = {}

def update_progress_bar(bar_length=50, max_lines=10):
    with progress_lock:
        # Clear the area where progress bars are displayed
        sys.stdout.write("\x1b[s")  # Save cursor position
        for i in range(max_lines):
            sys.stdout.write(f"\x1b[{i + 1};0H")  # Move cursor
            sys.stdout.write("\x1b[2K")  # Clear the line

        # Redraw only active progress bars
        active_bars = 0
        for script_key in sorted(progress_dict.keys()):
            if script_key not in max_steps_dict or max_steps_dict[script_key] <= 0:
                continue

            if script_key not in progress_bar_positions:
                progress_bar_positions[script_key] = active_bars + 1  # Assign a new line position
            position = progress_bar_positions[script_key]

            # Calculate progress
            progress = progress_dict[script_key]
            max_steps = max_steps_dict[script_key]
            progress_percentage = (progress / max_steps) * 100
            filled_length = int(bar_length * progress_percentage // 100)
            progress_bar = '#' * filled_length + '-' * (bar_length - filled_length)

            # Draw the progress bar
            sys.stdout.write(f"\x1b[{position};0H")  # Move cursor
            print(f"{script_key} Progress: [{progress_bar}] {progress_percentage:.2f}%", end='')

            active_bars += 1

        sys.stdout.write("\x1b[u")  # Restore cursor position
        sys.stdout.flush()


def run_test(script, start_test_time, mode, client_total, client_id):
    script_progress_key = f"{script}-{client_total}-{client_id}"
    params = [str(start_test_time), str(mode), str(client_total), str(client_id)]
    with progress_lock:
        # Initialize or reset the progress data at the start of the test
        max_steps_dict[script_progress_key] = 1  # Set to a default non-zero value
        progress_dict[script_progress_key] = 0
    with subprocess.Popen(["python", script] + params, stdout=subprocess.PIPE, text=True) as proc:
        first_message = True
        for line in proc.stdout:
            try:
                value = int(line.strip())
                with progress_lock:
                    if first_message:
                        max_steps_dict[script_progress_key] = value
                        progress_dict[script_progress_key] = 0
                        first_message = False
                    else:
                        progress_dict[script_progress_key] = value
                update_progress_bar()
            except ValueError:
                pass
    with progress_lock:
            if script_progress_key in progress_dict:
                # Mark as completed by setting the progress to the max steps
                progress_dict[script_progress_key] = max_steps_dict[script_progress_key]

def get_config_value(config, config_key):
    if config_key not in config:
        return None
    else:
        return config[config_key]
    
def execute_scripts(all_script, start_test_time, number_of_clients, mode, client_offset = 0):
    # Iterate over the range of client numbers
    for client_total in range(1, number_of_clients + 1):
        # Create a ThreadPoolExecutor with a number of workers equal to client_total * number of scripts
        with concurrent.futures.ThreadPoolExecutor(max_workers=client_total * len(all_script)) as executor:
            # Initialize a list to hold all futures
            futures = []
            print("\x1b[2J\x1b[H", end='')
            progress_dict.clear()
            max_steps_dict.clear()
            # Submitting run_test for each script with the current number of clients
            for script in all_script:
                for client_id in range(1, (client_total+client_offset) + 1):
                    future = executor.submit(run_test, script, start_test_time, mode, client_total, client_id)
                    futures.append(future)

            # Wait for all the futures to complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()  # Get the result of each future
            # Results can be processed here

def clear_screen():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For Unix-based systems (Linux, macOS, etc.)
    else:
        _ = os.system('clear')

def main():
    config = None
    logging.basicConfig(filename='test.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    if config is None:
        print('No config found!')
        exit(1)
    
    if 'pv-protocol' not in config:
        print('No protocol specified in config!')
        exit(1)

    if len(sys.argv) > 1:
        for i, param in enumerate(sys.argv[1:], start=1):
            if i == 1:
                index_offset = int(param)

    pv_protocol = get_config_value(config, 'pv-protocol')
    number_of_clients = get_config_value(config, 'number-of-client')
    if number_of_clients is None:
        print('No number of client found found!')
        exit(1)

    #create folder with the start test time
    start_test_time = 'test_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.mkdir(start_test_time) 

    # Running scripts sequentially
    print("Execute tests")
    progress_dict.clear()
    max_steps_dict.clear()
    all_script = [
        "test-epics-pv.py"
    ]
    if pv_protocol == 'pva':
        all_script[0] = "test-epics-pva.py"
    execute_scripts(all_script, start_test_time, number_of_clients, 'sequential', index_offset)
    
    # Clear the progress for the new set of tests
    # progress_dict.clear()
    # max_steps_dict.clear()
    # all_script = [
    #     "test-k2eg-pv.py"
    # ]
    execute_scripts(all_script, start_test_time, number_of_clients, 'sequential', index_offset)

    # progress_dict.clear()
    # max_steps_dict.clear()
    # all_script = [
    #     "test-epics-pv.py",
    #     "test-k2eg-pv.py"
    # ]
    # execute_scripts(all_script, start_test_time, number_of_clients, 'parallels')
    clear_screen()
    print("\ntest compelted!")
if __name__ == "__main__":
    main()