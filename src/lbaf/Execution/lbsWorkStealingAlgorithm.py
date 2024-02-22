import simpy
import random
from logging import Logger
from collections import deque

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsRank import Rank
from ..Model.lbsObject import Object


##################################################
########          Helper classes          ########
##################################################


class StealRequest():
    def __init__(self, r_snd: Rank, r_rcv: Rank):
        """Creates a steal request where r_snd steals a cluster from r_rcv"""
        self.__r_snd = r_snd
        self.__r_rcv = r_rcv

    def get_requesting_rank(self):
        return self.__r_snd

    def get_target_rank(self):
        return self.__r_rcv


class RankWorker(object):
    def __init__(self, env, rank_id, algorithm, lgr: Logger):
        """Class that handles all transfers, steals, and executions of tasks on a rank."""
        # Set up simpy environment
        self.env = env
        self.action = env.process(self.run())

        # Initialize logger and algorithm
        self.__logger = lgr
        self.algorithm = algorithm

        # Initialize rank information
        self.rank_id = rank_id

        # Output initial information
        initial_work = self.__get_total_work()
        self.__logger.info(f"id={self.rank_id}: total initial work={initial_work}, initial size={len(self.algorithm.rank_queues[self.rank_id])}")

    def run(self):
        """Defines the process that the simpy environment will run."""
        while self.algorithm.any_ranks_have_work() if self.algorithm.do_stealing else self.__has_work():
            if self.__has_work():
                # Get next object in queue
                item = self.algorithm.rank_queues[self.rank_id].popleft()

                # Execute task if it's an Object
                if isinstance(item, Object):

                    # If there is a shared block, find all other objects with that id and bring them to the front of the queue
                    sb_id = item.get_shared_block_id()
                    if sb_id is not None:
                        all_objs_in_cluster = []
                        for o in self.algorithm.rank_queues[self.rank_id]:
                            if isinstance(o, Object) and o.get_shared_block_id() == sb_id:
                                all_objs_in_cluster.append(o)
                        for o in all_objs_in_cluster:
                            self.algorithm.rank_queues[self.rank_id].insert(0, o) # Move all objects to the front of the queue

                    # Then execute the task
                    yield self.env.process(self.__simulate_task(item))

                # If item is a cluster, break into objects and move to front of the queue
                elif isinstance(item, list):
                    for o in item:
                        self.algorithm.rank_queues[self.rank_id].insert(0,o)

                    # Then execute the current task
                    task = self.algorithm.rank_queues[self.rank_id].popleft()
                    yield self.env.process(self.__simulate_task(task))

                # If item is a Steal Request, look for clusters to give up
                elif isinstance(item, StealRequest):
                    self.algorithm.respond_to_steal_request(item)
                    yield self.env.timeout(self.algorithm.steal_time) # is self.algorithm.steal_time right here?

                # Catch any errors
                else:
                    self.__logger.info(f"Received some other datatype: {type(item)}")

            # If no work available, request a steal from a random rank
            else:
                target_rank_id = random.randrange(0, self.algorithm.num_ranks)
                requesting_rank = self.algorithm.ranks[self.rank_id]
                target_rank = self.algorithm.ranks[target_rank_id]
                if self.algorithm.has_work(target_rank):
                    steal_request = StealRequest(requesting_rank, target_rank)
                    # Place steal request in target's queue
                    self.algorithm.rank_queues[target_rank_id].append(steal_request)
                    yield self.env.timeout(self.algorithm.steal_time)

    def __get_total_work(self):
        """Returns the total work on the rank."""
        total_work = 0.
        for item in self.algorithm.rank_queues[self.rank_id]:
            if isinstance(item, Object):
                total_work += item.get_load()
            elif isinstance(item, list):
                for o in item:
                    total_work += o.get_load()
            else:
                pass
        return total_work

    def __has_work(self):
        """Returns True if the rank has an object, cluster, or StealRequest in its queue."""
        return len(self.algorithm.rank_queues[self.rank_id]) > 0

    def __simulate_task(self, task: Object):
        """Simulates the execution of a task"""
        self.__logger.info(f"Rank {self.rank_id}: executing task {task.get_id()} (load {task.get_load()}) at time {self.env.now}")
        yield self.env.timeout(task.get_load())


#################################################
########        Algorithm class        ########
#################################################


class WorkStealingAlgorithm(AlgorithmBase):
    """A class for simulating work stealing for memory-constrained problems."""
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
        super(WorkStealingAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Initialize the discretion interval
        self.__discretion_interval = parameters.get("discretion_interval")
        self.steal_time = parameters.get("steal_time", 0.1)

        # Initialize logger
        self.__logger = lgr

        # Initialize rank information
        self.ranks = {}
        self.num_ranks = 0
        self.rank_queues = {}

        # Initialize the number of experiments and experiment times
        self.__num_experiments = parameters.get("num_experiments", 10)
        self.__experiment_times = []

        # Initialize do_stealing
        self.do_stealing = parameters.get("do_stealing", True)

    def __build_rank_clusters(self, rank: Rank, with_nullset) -> dict:
        """Cluster migratiable objects by shared block ID when available."""
        # Iterate over all migratable objects on rank
        clusters = {None: []} if with_nullset else {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb = o.get_shared_block()
            if sb is None:
                continue

            # Add current object to its block ID cluster
            clusters.setdefault(sb.get_id(), []).append(o)

        # Return dict of computed object clusters possibly randomized
        return {k: clusters[k] for k in random.sample(clusters.keys(), len(clusters))}

    def __initialize_rank_queues(self):
        """Populates every rank's deque with all initial clusters."""
        for r in self.ranks.values():
            rank_clusters = self.__build_rank_clusters(r, False)
            self.rank_queues[r.get_id()] = deque(cluster for cluster in rank_clusters.values())

    def respond_to_steal_request(self, steal_request: StealRequest):
        '''Resolves steal requests; if there is a cluster at the back of the receiving rank's queue, it is relocated to the sending rank's queue.'''
        # Get both ranks
        r_snd = steal_request.get_requesting_rank()
        r_rcv = steal_request.get_target_rank()

        # Check that r_rcv still has work
        if self.has_work(r_rcv):

            # If back of queue is a list (i.e. a cluster), allow steal
            if isinstance(self.rank_queues[r_rcv.get_id()][-1], list):
                cluster = self.rank_queues[r_rcv.get_id()].pop()
                self.rank_queues[r_snd.get_id()].append(cluster)

    def has_work(self, rank):
        """Determines if a given rank has an object, cluster, or StealRequest in its deque."""
        return len(self.rank_queues[rank.get_id()]) > 0

    def any_ranks_have_work(self):
        """Determines if any rank has an object, cluster, or StealRequest in its deque."""
        for r in self.ranks.values():
            if self.has_work(r):
                return True
        return False

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """Performs the simulation and returns the average time to complete all tasks."""
        # Initialize algorithm
        self._initialize(p_id, phases, distributions, statistics)
        ranks_list = self._rebalanced_phase.get_ranks()
        self.ranks = {rank.get_id(): rank for rank in ranks_list}
        self.num_ranks = len(self.ranks)
        self.__initialize_rank_queues()

        experiment_times = []

        for exp in range(self.__num_experiments):
            random.seed()

            workers = []

            env = simpy.Environment()

            for i in range(self.num_ranks):
                workers.append(RankWorker(env, i, self, self.__logger))

            env.run()
            end_time = env.now
            self.__logger.info(f"simulation finished at time {end_time}")

            experiment_times.append(end_time)

        self.__logger.info(f"Average time: {sum(experiment_times)/len(experiment_times)}")

