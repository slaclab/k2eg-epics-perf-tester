import time
import yaml

def test_k2eg(config):
    if 'pv-to-test' not in config:
        print('No pv configured')
    print(3, flush=True)
    for i in range(1, 4):
        print(i, flush=True)
        time.sleep(1)
    pv_list = config['pv-to-test']
    with open("test_k2eg_results.txt", "a") as file:
        file.write("ok" + "\n")

if __name__ == "__main__":
    config = None
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    test_k2eg(config)