import os
import sys


def stepper_test():
    log_file = sys.argv[1]
    if not os.path.isfile(log_file):
        print(f"File: {log_file} does not exist!")
        sys.exit(1)

    with open(log_file, 'r') as logger_output:
        output_str = logger_output.read()
        regex_list = [
            "cardinality: 32  sum: 10.5817  imbalance: 0.992173",
            "cardinality: 32  sum: 0.642948  imbalance: 4.91849",
            "cardinality: 32  sum: 0.526383  imbalance: 0.221116",
            "cardinality: 32  sum: 0.521197  imbalance: 0.0442304",
            "cardinality: 32  sum: 0.52225  imbalance: 0.0461051",
            "cardinality: 32  sum: 0.520378  imbalance: 0.0469951",
            "cardinality: 32  sum: 0.520078  imbalance: 0.0430356",
            "cardinality: 32  sum: 0.520286  imbalance: 0.0532831",
            "cardinality: 32  sum: 0.520617  imbalance: 0.0466161",
            "cardinality: 32  sum: 0.547612  imbalance: 1.44446",
            "cardinality: 32  sum: 0.522944  imbalance: 0.098434",
        ]
        for reg in regex_list:
            if reg in output_str:
                print(f"Found {reg}")
            else:
                print(f"Regex: {reg} not found in log.\nTEST FAILED.")
                sys.exit(1)


if __name__ == "__main__":
    stepper_test()
