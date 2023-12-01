import subprocess

def run_test(test_script):
    try:
        subprocess.run(["python", test_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running {test_script}")

def main():
    test_scripts = ["test-epics-pv.py", "test-k2eg-pv.py"]  # Add more scripts as needed
    for script in test_scripts:
        run_test(script)

if __name__ == "__main__":
    main()
