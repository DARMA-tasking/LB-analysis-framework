import random
import time
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..IO.lbsStatistics import print_function_statistics


class PrescribedPermutationAlgorithm(AlgorithmBase):
    """A concrete class for the algorithm to perform a prescribed object permutation."""

    def __init__(
        self,
        work_model,
        parameters: dict,
        lgr: Logger,
        rank_qoi: str,
        object_qoi: str):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param rank_qoi: rank QOI to track
        :param object_qoi: object QOI to track.
        """
        # Call superclass init
        super(PrescribedPermutationAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Retrieve mandatory parameters
        self.__permutation = parameters.get("permutation")
        if not isinstance(self.__permutation, dict) or not all(
                isinstance(i, int) for i in self.__permutation.values()):
            self._logger.error(f"Incorrect prescribed permutation: {self.__permutation}")
            raise SystemExit(1)

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Apply prescribed permutation to phase objects."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)
        if (l_p := len(self.__permutation)) != len(self._rebalanced_phase.get_objects()):
            self._logger.error(
                f"Permutation length ({l_p}) does not match number"
                f" of objects in phase ({len(self.__permutation)})")
            raise SystemExit(1)
        print_function_statistics(
            self._rebalanced_phase.get_ranks(),
            self._work_model.compute,
            "initial rank work",
            self._logger)

        # Index set of ranks
        ranks = {r.get_id(): r for r in self._rebalanced_phase.get_ranks()}
        n_r = len(ranks)

        # Iterate over ranks
        for r_src in ranks.values():
            # Iterate over objects on rank
            for o in r_src.get_objects():
                # Verify existence of assignment for object
                o_id = o.get_id()
                if (dst_id := self.__permutation.get(
                        o_id, -1)) < 0 or dst_id >= n_r:
                    self._logger.error(
                        f"Invalid assignment of object {o_id} to rank {dst_id}")
                    raise SystemExit(1)

                # Transfer object to prescribed rank
                print(o_id, ":", r_src.get_id(), "|->", dst_id)
                self._rebalanced_phase.transfer_object(
                    r_src, o, ranks.get(dst_id))

        # Compute and report post-permutation work statistics
        stats = print_function_statistics(
            self._rebalanced_phase.get_ranks(),
            self._work_model.compute,
            f"post-permutation rank work",
            self._logger)

        # Update run distributions and statistics
        self._update_distributions_and_statistics(distributions, statistics)
        print(statistics)
        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
