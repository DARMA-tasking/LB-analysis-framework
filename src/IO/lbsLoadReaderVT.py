#
#@HEADER
###############################################################################
#
#                              lbsLoadReaderVT.py
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
########################################################################
import csv
import os
import sys

import bcolors

from ..Model import Object, Processor


class LoadReader:
    """A class to read VT Object Map files. These CSV files conform
    to the following format:

      <time_step/phase>, <object-id>, <time>
      <time_step/phase>, <object-id1>, <object-id2>, <num-bytes>

    Each file is named as <base-name>.<node>.vom, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that is
    currently mapped to that VT node for a given time_step/phase. Lines with 3
    entries specify load for an object in term of wall time. Lines with 4
    entries specify the communication volume between objects in bytes.

    Load profile collection and output is enabled in VT with the following flags:

      mpirun -n 4 ./program --vt_lb_stats
                            --vt_lb_stats_dir=my-stats-dir
                            --vt_lb_stats_file=<base-name>
    """

    CommCategory = {
        "SendRecv": 1,
        "CollectionToNode": 2,
        "NodeToCollection": 3,
        "Broadcast": 4,
        "CollectionToNodeBcast": 5,
        "NodeToCollectionBcast": 6,
        }

    def __init__(self, file_prefix, verbose=False):
        # The base directory and file name for the log files
        self.file_prefix = file_prefix

        # Enable or disable verbose mode
        self.verbose = verbose

    def get_node_trace_file_name(self, node_id):
        """Build the file name for a given rank/node ID
        """

        return "{}.{}.vom".format(
            self.file_prefix, node_id)

    def read(self, node_id, time_step=-1, comm=False):
        """Read the file for a given node/rank. If time_step==-1 then all
        steps are read from the file; otherwise, only `time_step` is.
        """

        # Retrieve file name for given node and make sure that it exists
        file_name = self.get_node_trace_file_name(node_id)
        print(bcolors.HEADER
            + "[LoadReaderVT] "
            + bcolors.END
            + "Reading {} VT object map".format(file_name))
        if not os.path.isfile(file_name):
            print(bcolors.ERR
                + "*  ERROR: [LoadReaderVT] File {} does not exist.".format(file_name)
                + bcolors.END)
            sys.exit(1)

        # Initialize storage
        iter_map = dict()

        # Open specified input file
        with open(file_name, 'r') as f:
            log = csv.reader(f, delimiter=',')
            # Iterate over rows of input file
            print(log)
            for row in log:
                n_entries = len(row)
                print(row)
                # Handle three-entry case that corresponds to an object load
                if '[' in row[4]:
                    # Parsing the three-entry case, thus this format:
                    #   <time_step/phase>, <object-id>, <time>, <#-subphases> '[' 
                    #   [<subphase-time-1>] ... [<subphase-time-N>] ']'
                    # Converting these into integers and floats before using them or
                    # inserting the values in the dictionary
                    try:
                        phase, o_id = map(int, row[:2])
                        time = float(row[2])
                        Nsubphases = int(row[3])
                        subphase_times = row[4]
                        subphase_times = subphase_times[1:-1].split(',')
                        subphase_times = [float(x) for x in subphase_times]
                        assert len(subphase_times) == Nsubphases
                    except:
                        print(bcolors.ERR
                            + "*  ERROR: [LoadReaderVT] Incorrect row format:".format(row)
                            + bcolors.END)

                    # Update processor if iteration was requested
                    if time_step in (phase, -1):
                        # Instantiate object with retrieved parameters
                        obj = Object(o_id, time, node_id)

                        # If this iteration was never encoutered initialize proc object
                        iter_map.setdefault(phase, Processor(node_id))

                        # Add object to processor
                        iter_map[phase].add_object(obj)

                        # Print debug information when requested
                        if self.verbose:
                            print(bcolors.HEADER
                                + "[LoadReaderVT] "
                                + bcolors.END
                                + "iteration = {}, object id = {}, time = {}, subphases = {}".format(
                                phase,
                                o_id,
                                time,
                                Nsubphases,
                                end=''))
                                
                            for i in range(0,Nsubphases):
                                print("subphase-time-" + str(i) + "= {}".format(
                                    row[4 + i],
                                end=''))
                                
                            print()

                # Handle four-entry case that corresponds to a communication weight
                elif n_entries == 4:
                    # Parsing the five-entry case, thus this format:
                    #   <time_step/phase>, <to-object-id>, <from-object-id>, <weight>, <comm-type>
                    # Converting these into integers and floats before using them or
                    # inserting the values in the dictionary
                    print(bcolors.ERR
                        + "*  ERROR: [LoadReaderVT] Communication graph unimplemented"
                        + bcolors.END)
                    sys.exit(1)
                    
                # Unrecognized line format
                else:
                    print(bcolors.ERR
                        + "** ERROR: [LoadReaderVT] Wrong line length: {}".format(row)
                        + bcolors.END)
                    sys.exit(1)

        # Print more information when requested
        if self.verbose:
            print(bcolors.HEADER
                + "[LoadReaderVT] "
                + bcolors.END
                + "Finished reading file: {}".format(file_name))

        # Return map of populated processors per iteration
        return iter_map

    def read_iteration(self, n_p, time_step):
        """Read all the data in the range of procs [0..n_p) for a given
        iteration `time_step`. Collapse the iter_map dictionary from `read(..)`
        into a list of processors to be returned for the given iteration.
        """
        
        # Create storage for processors
        procs = [None] * n_p

        # Iterate over all processors
        for p in range(n_p):
            # Read data for given iteration and assign it to processor
            proc_iter_map = self.read(p, time_step)

            # Try to retrieve processor information at given time-step
            try:
                procs[p] = proc_iter_map[time_step]
            except KeyError:
                print(bcolors.ERR
                    + "*  ERROR: [LoadReaderVT] Could not retrieve information for processor {} at time_step {}".format(
                    p,
                    time_step)
                    + bcolors.END)
                sys.exit(1)
            
        # Return populated list of processors
        return procs
