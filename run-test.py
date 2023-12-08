import os
import subprocess
import concurrent.futures
import threading
import time
import datetime
import sys
import pandas as pd
import matplotlib.pyplot as plt
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


def run_test(test_script, params=[]):
    with subprocess.Popen(["python", test_script] + params, stdout=subprocess.PIPE, text=True) as proc:
        first_message = True
        for line in proc.stdout:
            try:
                value = int(line.strip())
                with progress_lock:
                    if first_message:
                        max_steps_dict[test_script] = value
                        progress_dict[test_script] = 0
                        first_message = False
                    else:
                        progress_dict[test_script] = value
                update_progress_bar()
            except ValueError:
                pass
    with progress_lock:
        if test_script in progress_dict:
            del progress_dict[test_script]
        if test_script in max_steps_dict:
            del max_steps_dict[test_script]

def main():
    #create folder with the start test time
    start_test_time = 'test_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.mkdir(start_test_time) 

    # Running scripts sequentially
    sequential_scripts = [
        ("test-epics-pv.py", [start_test_time, "standalone"]),
        ("test-k2eg-pv.py", [start_test_time, "standalone"])
    ]

    print("Execute sequential tests")
    for script, params in sequential_scripts:
        print(f"\nExecute {script} tests")
        run_test(script, params)

    # Clear the progress for the new set of tests
    progress_dict.clear()
    max_steps_dict.clear()

    # Running scripts in parallel
    parallel_scripts = [
        ("test-epics-pv.py", [start_test_time, "combined"]),
        ("test-k2eg-pv.py", [start_test_time, "combined"])
    ]
    print("\nExecute parallels tests")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_test, script, params) for script, params in parallel_scripts]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    print("\ntest compelted!")
if __name__ == "__main__":
    main()