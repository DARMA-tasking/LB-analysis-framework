#
#@HEADER
###############################################################################
#
#                             lbsJSONTaskLister.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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
"""
Utility to generate a yaml containing lists of tasks associated to their respective ranks,
from the last phase and last sub-iteration of input JSON files.

"""

import os
import sys
import json
import yaml
import argparse
import re

from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.Utils.lbsLogging import get_logger, Logger

def process_files(directory, file_stem, file_suffix, logger: Logger):
    reader = LoadReader(
        file_prefix = directory + file_stem,
        logger = logger,
        file_suffix = file_suffix
    )

    tasks = {}
    n_ranks = reader.n_ranks

    try:
        for rank in range(n_ranks):
            _, data = reader._load_vt_file(rank)
            phases = data.get("phases", [])
            if not phases:
                logger.warning("No phases found for rank %s", str(rank))
                continue

            last_phase = phases[-1]

            if "lb_iterations" in last_phase:
                lb_iterations = last_phase["lb_iterations"]
                if lb_iterations:
                    last_lb_iteration = lb_iterations[-1]
                    iteration_tasks = [task["entity"].get("seq_id", task["entity"].get("id")) for task in last_lb_iteration.get("tasks", [])]
                    tasks[rank] = iteration_tasks
                else:
                    logger.warning("No lb_iterations found in the last phase of rank %s", str(rank))
            else:
                phase_tasks = [task["entity"].get("seq_id", task["entity"].get("id")) for task in last_phase.get("tasks", [])]
                tasks[rank] = phase_tasks
    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
        logger.error("Error processing rank %s: %s", str(rank), e)
        sys.exit(1)

    return tasks

def main():
    parser = argparse.ArgumentParser(description="Extract tasks from JSON files.")
    parser.add_argument("directory", type=str, help="Directory containing JSON files.")
    parser.add_argument("--file-stem", type=str, default="data", help="File stem for JSON files (default: 'data').")
    parser.add_argument("--file-suffix", type=str, default="json", help="File suffix for JSON files (default: 'json').")
    parser.add_argument("--output", type=str, default="tasks.yml", help="Output YAML file (default: 'tasks.yml').")

    args = parser.parse_args()

    directory = args.directory
    file_stem = args.file_stem
    file_suffix = args.file_suffix
    output_file = args.output

    logger = get_logger()

    if not os.path.isdir(directory):
        logger.error("Directory not found: %s", directory)
        return

    tasks = process_files(directory, file_stem, file_suffix, logger)

    try:
        with open(output_file, 'w') as file:
            yaml.safe_dump(tasks, file)
        logger.info("Tasks successfully written to %s", output_file)
    except IOError as e:
        logger.error("Error writing to %s: %s", output_file, e)

if __name__ == "__main__":
    main()
