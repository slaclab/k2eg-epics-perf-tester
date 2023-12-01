
import json
import logging
import sys
import os
import time
from epics import PV

def monitor_handler(pvname=None, data=None, timestamp=None, **kwargs):
    current_time_nanoseconds = time.time_ns()

    # Convert the PV timestamp to nanoseconds
    pv_timestamp_nanoseconds = int(timestamp * 1e9)

    # Calculate latency in seconds and nanoseconds
    latency_nanoseconds = current_time_nanoseconds - pv_timestamp_nanoseconds

    # Adjust for nanosecond overflow/underflow
    if latency_nanoseconds < 0:
        latency_nanoseconds += 1e9

    print(f"PV:{pvname} latency  nanousec:{latency_nanoseconds}")
    

if __name__ == "__main__":
    pv = PV('VPIO:IN20:111:VRAW', callback=monitor_handler)

    # Ensure connection
    if not pv.wait_for_connection(timeout=5):
        print("Failed to connect to PV within timeout.")
        exit()

    # Keep the script running to monitor the PV
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")