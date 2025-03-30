from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import print_function_statistics


class PrescribedPermutationAlgorithm(AlgorithmBase):
    """A concrete class for the algorithm to perform a prescribed object permutation."""

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

        # Retrieve mandatory parameters
        self.__permutation = parameters.get("permutation")
        if not isinstance(self.__permutation, dict) or not all(
                isinstance(i, int) for i in self.__permutation.values()):
            self._logger.error(f"Incorrect prescribed permutation: {self.__permutation}")
            raise SystemExit(1)

    def execute(self, p_id: int, phases: list, statistics: dict):
        """ Apply prescribed permutation to phase objects."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, statistics)
        objects = self._rebalanced_phase.get_objects()
        if (l_p := len(self.__permutation)) != len(objects):
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

        # Iterate over objects
        for o in objects:
            # Verify existence of assignment for object
            o_id = o.get_id()
            if (dst_id := self.__permutation.get(
                    o_id, -1)) < 0 or dst_id >= n_r:
                self._logger.error(
                    f"Invalid assignment of object {o_id} to rank {dst_id}")
                raise SystemExit(1)

            # Transfer object to prescribed rank
            r_src = ranks[o.get_rank_id()]
            self._logger.debug(
                f"object {o_id}: rank {r_src.get_id()} |-> rank {dst_id}")
            self._rebalanced_phase.transfer_object(
                r_src, o, ranks.get(dst_id))

        # Compute and report post-permutation work statistics
        _ = print_function_statistics(
            self._rebalanced_phase.get_ranks(),
            self._work_model.compute,
            "post-permutation rank work",
            self._logger)

        # Update run statistics
        self._update_statistics(statistics)

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
