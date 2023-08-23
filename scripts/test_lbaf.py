import os
import sys


def run_tests():
    imbalance_file = sys.argv[1]
    if not os.path.isfile(imbalance_file):
        print(f"File: {imbalance_file} does not exist!")
        sys.exit(1)

    with open(imbalance_file, 'r', encoding="utf-8") as imb_file:
        imb_level = float(imb_file.read())
        print(f"@@@@@ FOUND IMBALANCE: {imb_level} @@@@@")
        if imb_level < 0.000001:
            print("===> TEST PASSED!")
        else:
            print("===> TEST FAILED!")
            sys.exit(1)


if __name__ == "__main__":
    run_tests()
