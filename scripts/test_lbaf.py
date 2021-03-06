#@HEADER
###############################################################################
#
#                                test_lbaf.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
###############################################################################
import subprocess
import sys

import bcolors

# Provide tests commands to TEST_COMMANDS.
# Last word in the command should be the output directory. Then inbalance is checked.
TESTS_COMMANDS = [
    ["python", "/lbaf/src/Applications/LBAF.py", "-l", "/lbaf/data/vt_example_lb_stats/stats", "-x", "4",
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
