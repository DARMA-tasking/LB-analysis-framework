#
#@HEADER
###############################################################################
#
#                              lbsLoadWriterVT.py
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
import json
from logging import Logger
import os

import brotli

from src.Model.lbsPhase import Phase
from src.Model.lbsRank import Rank
from src.Utils.logger import CLRS


class LoadWriterVT:
    """A class to write load directives for VT as JSON files with
    the following format:

      <iter/phase>, <object-id>, <time>

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that must
    be mapped to that VT node for a given iteration/phase.
    """

    def __init__(self, phase: Phase, f="lbs_out", s="vom", output_dir=None, logger: Logger = None):
        """Class constructor:
        phase: Phase instance
        f: file name stem
        s: suffix
        """
        # Assign logger to instance variable
        self.lgr = logger
        # Assign colors for logger
        self.grn = CLRS.get('green')
        self.red = CLRS.get('red')

        # Ensure that provided phase has correct type
        if not isinstance(phase, Phase):
            self.lgr.error(self.red(f"Could not write to ExodusII file by lack of a LBS phase"))
            return

        # Assign internals
        self.phase = phase
        self.file_stem = "{}".format(f)
        self.suffix = s
        self.output_dir = output_dir

    def write(self):
        """Write one JSON file per rank with the following format:
            <phase-id>, <object-id>, <time>
        """
        # Iterate over ranks
        for p in self.phase.ranks:
            # Create file name for current rank
            file_name = f"{self.file_stem}.{p.get_id()}.{self.suffix}"

            if self.output_dir is not None:
                file_name = os.path.join(self.output_dir, file_name)

            # Count number of unsaved objects for sanity
            n_u = 0

            self.json_writer(file_name=file_name, n_u=n_u, rank=p)

    def json_writer(self, file_name: str, n_u: int, rank: Rank):
        temp_dict = {}
        # Iterate over objects
        for o in rank.get_objects():
            # Write object to file and increment count
            try:
                # writer.writerow([o.get_rank_id(), o.get_id(), o.get_time()])
                proc_id = o.get_rank_id()
                obj_id = o.get_id()
                obj_time = o.get_time()
                if isinstance(temp_dict.get(proc_id, None), list):
                    temp_dict[proc_id].append({'proc_id': proc_id, 'obj_id': obj_id, 'obj_time': obj_time})
                else:
                    temp_dict[proc_id] = list()
                    temp_dict[proc_id].append({'proc_id': proc_id, 'obj_id': obj_id, 'obj_time': obj_time})
            except:
                n_u += 1

        dict_to_dump = {}
        dict_to_dump['phases'] = list()
        for proc_id, others_list in temp_dict.items():
            phase_dict = {'tasks': list(), 'id': proc_id}
            for task in others_list:
                task_dict = {'time': task['obj_time'], 'resource': 'cpu', 'object': task['obj_id']}
                phase_dict['tasks'].append(task_dict)
            dict_to_dump['phases'].append(phase_dict)

        json_str = json.dumps(dict_to_dump, separators=(',', ':'))
        compressed_str = brotli.compress(string=json_str.encode('utf-8'), mode=brotli.MODE_TEXT)

        with open(file_name, 'wb') as compr_json_file:
            compr_json_file.write(compressed_str)

        # Sanity check
        if n_u:
            self.lgr.error(self.red(f"{n_u} objects could not be written to JSON file {file_name}"))
        else:
            self.lgr.info(self.grn(f"Wrote {len(rank.get_objects())} objects to {file_name}"))
