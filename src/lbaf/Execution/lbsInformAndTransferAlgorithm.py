#
#@HEADER
###############################################################################
#
#                       lbsInformAndTransferAlgorithm.py
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
import random
import time
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import min_Hamming_distance, print_function_statistics


class InformAndTransferAlgorithm(AlgorithmBase):
    """A concrete class for the 2-phase gossip+transfer algorithm."""

    def __init__(
        self,
        work_model,
        parameters: dict,
        lgr: Logger):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        """
        # Call superclass init
        super().__init__(work_model, parameters, lgr)

        # Retrieve mandatory integer parameters
        self.__n_iterations = parameters.get("n_iterations")
        if not isinstance(self.__n_iterations, int) or self.__n_iterations < 0:
            self._logger.error(f"Incorrect provided number of algorithm iterations: {self.__n_iterations}")
            raise SystemExit(1)
        self.__n_rounds = parameters.get("n_rounds")
        if not isinstance(self.__n_rounds, int) or self.__n_rounds < 0:
            self._logger.error(f"Incorrect provided number of information rounds: {self.__n_rounds}")
            raise SystemExit(1)
        self.__fanout = parameters.get("fanout")
        if not isinstance(self.__fanout, int) or self.__fanout < 0:
            self._logger.error(f"Incorrect provided information fanout {self.__fanout}")
            raise SystemExit(1)
        self._logger.info(
            f"Instantiated with {self.__n_iterations} iterations, {self.__n_rounds} rounds, fanout {self.__fanout}")

        # Try to instantiate object transfer criterion
        crit_name = parameters.get("criterion")
        self.__transfer_criterion = CriterionBase.factory(
            crit_name,
            self._work_model,
            logger=self._logger)
        if not self.__transfer_criterion:
            self._logger.error(f"Could not instantiate a transfer criterion of type {crit_name}")
            raise SystemExit(1)

        # Try to instantiate object transfer strategy
        strat_name = parameters.get("transfer_strategy")
        self.__transfer_strategy = TransferStrategyBase.factory(
            strat_name.title(),
            parameters,
            self.__transfer_criterion,
            logger=self._logger)
        if not self.__transfer_strategy:
            self._logger.error(f"Could not instantiate a transfer strategy of type {strat_name}")
            raise SystemExit(1)

        # No information about peers is known initially
        self.__known_peers = {}

        # Optional target imbalance for early termination of iterations
        self.__target_imbalance = parameters.get("target_imbalance", 0.0)

    def get_known_peers(self):
        """Return all known peers."""
        return self.__known_peers

    def __process_message(self, r_rcv: Rank, m: Message):
        """Process message received by rank."""
        # Make rank aware of itself
        if r_rcv not in self.__known_peers:
            self.__known_peers[r_rcv] = {r_rcv}

        # Process the message
        self.__known_peers[r_rcv].update(m.get_support())

    def __forward_message(self, i: int, r_snd: Rank, f: int):
        """Forward information message to rank peers sampled from known ones."""
        # Make rank aware of itself
        if r_snd not in self.__known_peers:
            self.__known_peers[r_snd] = {r_snd}

        # Create load message tagged at given information round
        msg = Message(i, self.__known_peers[r_snd])

        # Compute complement of set of known peers
        complement = self.__known_peers[r_snd].difference({r_snd})

        # Forward message to pseudo-random sample of ranks
        return random.sample(
            list(complement), min(f, len(complement))), msg

    def __execute_information_stage(self):
        """Execute information stage."""
        # Build set of all ranks in the phase
        rank_set = set(self._rebalanced_phase.get_ranks())

        # Initialize information messages and known peers
        messages, self.__known_peers = {}, {}
        n_r = len(rank_set)
        for r_snd in rank_set:
            # Make rank aware of itself
            self.__known_peers[r_snd] = {r_snd}

            # Create initial message spawned from rank
            msg = Message(0, {r_snd})

            # Broadcast message to random sample of ranks excluding self
            for r_rcv in random.sample(
                list(rank_set.difference({r_snd})), min(self.__fanout, n_r - 1)):
                messages.setdefault(r_rcv, []).append(msg)

        # Sanity check prior to forwarding iterations
        if (n_m := sum(len(m) for m in messages.values())) != (n_c := n_r * self.__fanout):
            self._logger.error(
                f"Incorrect number of initial messages: {n_m} <> {n_c}")
        self._logger.info(
            f"Sent {n_m} initial information messages with fanout={self.__fanout}")

        # Process all received initial messages
        for r_rcv, m_rcv in messages.items():
            for m in m_rcv:
                # Process message by recipient
                self.__process_message(r_rcv, m)

        # Perform sanity check on first round of information aggregation
        n_k = 0
        for r in rank_set:
            # Retrieve and tally peers known to rank
            k_p = self.__known_peers.get(r, {})
            n_k += len(k_p)
            self._logger.debug(
                f"Peers known to rank {r.get_id()}: {[r_k.get_id() for r_k in k_p]}")
        if n_k != (n_c := n_c + n_r):
            self._logger.error(
                f"Incorrect total number of aggregated initial known peers: {n_k} <> {n_c}")

        # Forward messages for as long as necessary and requested
        for i in range(1, self.__n_rounds):
            # Initiate next information round
            self._logger.debug(f"Performing message forwarding round {i}")
            messages.clear()

            # Iterate over all ranks
            for r_snd in rank_set:
                # Collect message when destination list is not empty
                dst, msg = self.__forward_message(
                    i, r_snd, self.__fanout)
                for r_rcv in dst:
                    messages.setdefault(r_rcv, []).append(msg)

            # Process all messages of first round
            for r_rcv, msg_lst in messages.items():
                for m in msg_lst:
                    self.__process_message(r_rcv, m)

            # Report on known peers when requested
            for rank in rank_set:
                self._logger.debug(
                    f"Peers known to rank {rank.get_id()}: {[r_k.get_id() for r_k in k_p]}")

        # Report on final known information ratio
        n_k = sum(len(k_p) for k_p in self.__known_peers.values() if k_p) / n_r
        self._logger.info(
            f"Average number of peers known to ranks: {n_k} ({100 * n_k / n_r:.2f}% of {n_r})")

    def execute(self, p_id: int, phases: list, statistics: dict, a_min_max):
        """ Execute 2-phase information+transfer algorithm on Phase with index p_id."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, statistics)
        print_function_statistics(
            self._rebalanced_phase.get_ranks(),
            self._work_model.compute,
            "initial rank work",
            self._logger)

        # Set phase to be used by transfer criterion
        self.__transfer_criterion.set_phase(self._rebalanced_phase)

        # Retrieve total work from computed statistics
        total_work = statistics["total work"][-1]

        # Perform requested number of load-balancing iterations
        for i in range(self.__n_iterations):
            self._logger.info(f"Starting iteration {i + 1} with total work of {total_work}")

            # Time the duration of each iteration
            start_time = time.time()

            # Start with information stage
            self.__execute_information_stage()

            # Execute transfer stage
            n_ignored, n_transfers, n_rejects = self.__transfer_strategy.execute(
                self.__known_peers, self._rebalanced_phase, statistics[
                    "average load"], statistics["maximum load"][-1])
            if (n_proposed := n_transfers + n_rejects):
                self._logger.info(
                    f"Transferred {n_transfers} objects amongst {n_proposed} proposed "
                    f"({100. * n_rejects / n_proposed:.4}%)")
            else:
                self._logger.info("No proposed object transfers")

            # Report iteration statistics
            self._logger.info(
                f"Iteration {i + 1} completed ({n_ignored} skipped ranks) in {time.time() - start_time:.3f} seconds")

            # Compute and report iteration work statistics
            stats = print_function_statistics(
                self._rebalanced_phase.get_ranks(),
                self._work_model.compute,
                f"iteration {i + 1} rank work",
                self._logger)

            # Update run statistics
            self._update_statistics(statistics)

            # Retain load balancing iteration as a phase with sub-index
            lb_iteration = Phase(self._logger, p_id, None, i + 1)
            new_ranks: Set[Rank] = set()
            for r in self._rebalanced_phase.get_ranks():
                # Minimally instantiate rank and copy
                new_r = Rank(self._logger)
                new_r.copy(r)
                new_ranks.add(new_r)
            lb_iteration.set_ranks(new_ranks)
            lb_iteration.set_communications(self._initial_communications)
            self._initial_phase.get_lb_iterations().append(lb_iteration)

            # Report minimum Hamming distance when minimax optimum is available
            if a_min_max:
                # Compute current arrangement
                arrangement = dict(sorted(
                    {o.get_id(): p.get_id()
                     for p in self._rebalanced_phase.get_ranks()
                     for o in p.get_objects()}.items())).values()
                self._logger.debug(f"Iteration {i + 1} arrangement: {tuple(arrangement)}")

                # Compute minimum distance from arrangement to optimum
                hd_min = min_Hamming_distance(arrangement, a_min_max)
                self._logger.info(
                    f"Iteration {i + 1} minimum Hamming distance to optimal arrangements: {hd_min}")
                statistics["minimum Hamming distance to optimum"].append(hd_min)

            # Check if the current imbalance is within the target_imbalance range
            if stats.statistics["imbalance"] <= self.__target_imbalance:
                self._logger.info(
                    f"Reached target imbalance of {self.__target_imbalance} after {i + 1} iterations.")
                break

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
