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
Utility to generate a YAML file containing lists of tasks associated with their respective ranks,
from the last phase and last sub-iteration of input JSON files.
"""

import os
import json
import yaml
import argparse

from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.Utils.lbsLogging import get_logger, Logger
from typing import Optional

class JSONTaskLister:
    """
    A utility class to process JSON files, extract tasks for each rank, and save the results in a YAML file.
    """

    def __init__(self, logger: Optional[Logger] = None):
        """
        Initializes an instance of the JSONTaskLister class.

        Args:
            logger (Optional[Logger]): A logger instance for logging messages. If not provided, a default logger is used.
        """
        self.__logger = logger if logger is not None else get_logger()
        self.__directory = ""  # Directory containing the input JSON files
        self.__file_stem = "data"  # Default file stem for JSON files
        self.__file_suffix = "json"  # Default file suffix for JSON files
        self.__output_file = "tasks.yaml"  # Default name of the output YAML file

    def __process_files(self):
        """
        Processes the JSON files in the specified directory to extract tasks for each rank.

        Returns:
            dict: A dictionary where keys are ranks and values are lists of tasks.
        """
        # Initialize the JSON data reader
        reader = LoadReader(
            file_prefix=self.__directory + self.__file_stem,
            logger=self.__logger,
            file_suffix=self.__file_suffix
        )

        tasks = {}  # Dictionary to store tasks by rank
        n_ranks = reader.n_ranks  # Get the total number of ranks

        try:
            # Iterate over each rank
            for rank in range(n_ranks):
                _, data = reader._load_vt_file(rank)  # Load JSON data for the current rank
                phases = data.get("phases", [])  # Extract phases from the data

                if not phases:
                    self.__logger.warning(f"No phases found for rank {rank}")
                    continue

                last_phase = phases[-1]  # Get the last phase

                # Check if there are load balancing iterations in the last phase
                if "lb_iterations" in last_phase:
                    lb_iterations = last_phase["lb_iterations"]

                    if lb_iterations:
                        # Extract tasks from the last load balancing iteration
                        last_lb_iteration = lb_iterations[-1]
                        iteration_tasks = [
                            task["entity"].get("seq_id", task["entity"].get("id"))
                            for task in last_lb_iteration.get("tasks", [])
                        ]
                        tasks[rank] = iteration_tasks
                    else:
                        self.__logger.warning(f"No lb_iterations found in the last phase of rank {rank}")
                else:
                    # Extract tasks directly from the last phase if no lb_iterations exist
                    phase_tasks = [
                        task["entity"].get("seq_id", task["entity"].get("id"))
                        for task in last_phase.get("tasks", [])
                    ]
                    tasks[rank] = phase_tasks

        except (json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
            self.__logger.error(f"Error processing rank {rank}: {e}")
            return

        return tasks

    def run(self):
        """
        Main entry point for the JSONTaskLister utility. Parses command-line arguments,
        processes JSON files, and writes the extracted tasks to a YAML file.
        """
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Extract tasks from JSON files.")
        parser.add_argument("directory", type=str, help="Directory containing JSON files.")
        parser.add_argument("--file-stem", type=str, default="data", help="File stem for JSON files (default: 'data').")
        parser.add_argument("--file-suffix", type=str, default="json", help="File suffix for JSON files (default: 'json').")
        parser.add_argument("--output", type=str, default="tasks.yaml", help="Output YAML file (default: 'tasks.yml').")

        args = parser.parse_args()

        # Set instance variables based on parsed arguments
        self.__directory = args.directory
        self.__file_stem = args.file_stem
        self.__file_suffix = args.file_suffix
        self.__output_file = args.output

        # Validate the directory
        if not os.path.isdir(self.__directory):
            self.__logger.error(f"Directory not found: {self.__directory}")
            return

        # Process files and extract tasks
        tasks = self.__process_files()

        # Write the extracted tasks to the output YAML file
        try:
            with open(self.__output_file, 'w') as file:
                yaml.safe_dump(tasks, file)
            self.__logger.info(f"Tasks successfully written to {self.__output_file}")
        except IOError as e:
            self.__logger.error(f"Error writing to {self.__output_file}: {e}")
            return

if __name__ == "__main__":
    JSONTaskLister().run()
