import subprocess
import sys

import bcolors

# Provide tests commands to TEST_COMMANDS.
# Last word in the command should be the output directory. Then inbalance is checked.
TESTS_COMMANDS = [
    ["python", "/lbaf/src/Applications/NodeGossiper.py", "-l", "/lbaf/data/vt_example_lb_stats/stats", "-x", "4",
     "-y", "2", "-z", "1", "-s", "0", "-f", "4", "-k", "4", "-i", "4", "-c", "1", "-e", "-b", "/lbaf/output"],
]


def run_tests():
    for test_cmd in TESTS_COMMANDS:
        script = subprocess.run(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(script.stdout)
        if script.stderr:
            raise RuntimeError(f"Commands: {test_cmd}\nSTDERR: {script.stderr}")
        imbalance_file = f"{test_cmd[-1]}/imbalance.txt"
        with open(imbalance_file, 'r') as imb_file:
            imb_level = float(imb_file.read())
            if imb_level < 0.05:
                print(f"{bcolors.OKMSG}PASSED!\n=> TEST for INPUT {' '.join(test_cmd)}{bcolors.END}")
                print(f"{bcolors.OKMSG}------------------------------------------------------------{bcolors.END}")
            else:
                print(f"{bcolors.ERR}FAILED!\n=> TEST for INPUT {' '.join(test_cmd)}{bcolors.END}")
                print(f"{bcolors.ERR}------------------------------------------------------------{bcolors.END}")
                sys.exit(1)


if __name__ == "__main__":
    run_tests()
