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


class StealRequest:
    def __init__(self, r_snd: Rank, r_rcv: Rank):
        """Creates a steal request where r_snd steals a cluster from r_rcv"""
        self.__r_snd = r_snd
        self.__r_rcv = r_rcv

    def get_requesting_rank(self):
        return self.__r_snd

    def get_target_rank(self):
        return self.__r_rcv


class RankWorker:
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
        self.rank = self.algorithm.ranks[self.rank_id]

        # Output initial information
        initial_work = self.__get_total_work()
        self.__logger.info(f"  Rank {self.rank_id}: total initial work={initial_work}, initial size={len(self.algorithm.rank_queues[self.rank_id])}")

    def run(self):
        """Defines the process that will run within the simpy environment."""
        while self.algorithm.any_ranks_have_work() if self.algorithm.do_stealing else self.__has_work():
            if self.__has_work():
                # Get next object in queue
                item = self.algorithm.rank_queues[self.rank_id].popleft()

                # Execute task if it's an Object
                if isinstance(item, Object):

                    # If there is a shared block, find all other objects with that id and bring them to the front of the queue
                    sb_id = item.get_shared_block_id()
                    if sb_id is not None:
                        all_tasks_in_cluster = []
                        for task in self.algorithm.rank_queues[self.rank_id]:
                            if isinstance(task, Object) and task.get_shared_block_id() == sb_id:
                                all_tasks_in_cluster.append(task)
                        for task in all_tasks_in_cluster:
                            self.algorithm.rank_queues[self.rank_id].remove(task)
                            self.algorithm.rank_queues[self.rank_id].appendleft(task) # Move all tasks to the front of the queue

                    # Then execute the task
                    yield self.env.process(self.__simulate_task(item))

                # If item is a cluster, break into objects and move to front of the queue
                elif isinstance(item, list):
                    for o in item:
                        self.algorithm.rank_queues[self.rank_id].appendleft(o)

                    # Then execute the current task
                    task = self.algorithm.rank_queues[self.rank_id].popleft()
                    yield self.env.process(self.__simulate_task(task))

                # If item is a StealRequest, look for clusters to give up
                elif isinstance(item, StealRequest):
                    self.algorithm.respond_to_steal_request(item)
                    yield self.env.timeout(self.algorithm.steal_time) # is self.algorithm.steal_time right here?

                # Catch any errors
                else:
                    self.__logger.info(f"Received some other datatype: {type(item)}")

            # If no work available, request a steal from a random rank
            else:
                target_rank_id = random.randrange(0, self.algorithm.num_ranks)
                requesting_rank = self.rank
                target_rank = self.algorithm.ranks[target_rank_id]
                if self.algorithm.has_work(target_rank):
                    steal_request = StealRequest(requesting_rank, target_rank)
                    # Place steal request in target's queue
                    self.algorithm.rank_queues[target_rank_id].appendleft(steal_request)
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
        """Returns True if the rank has an object or cluster in its queue."""
        return self.algorithm.has_work(self.rank)

    def __simulate_task(self, task: Object):
        """Simulates the execution of a task"""
        self.algorithm.increment_task_count()
        self.__logger.info(f"    Rank {self.rank_id}: executing task {task.get_id()} (sb_id {task.get_shared_block_id()}, load {task.get_load()}) at time {self.env.now} ({self.algorithm.get_task_count()}/{self.algorithm.get_total_task_count()})")
        yield self.env.timeout(task.get_load())


#################################################
#########        Algorithm class        #########
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

        # Initialize task and steal counts
        self.__task_count = 0
        self.__total_task_count = 0
        self.__steal_count = 0
        self.__attempted_steal_count = 0

        # Initialize the number of experiments and experiment times
        self.__num_experiments = parameters.get("num_experiments", 10)
        self.__experiment_times = []

        # Initialize do_stealing
        self.do_stealing = parameters.get("do_stealing", True)

    def __build_rank_clusters(self, rank: Rank, with_nullset) -> dict:
        """Cluster migratable objects by shared block ID when available."""
        # Iterate over all migratable objects on rank
        clusters = {None: []} if with_nullset else {}
        non_clustered_tasks = []
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb = o.get_shared_block()
            if sb is None:
                non_clustered_tasks.append(o)
                self.__total_task_count += 1

            else:
                # Add current object to its block ID cluster
                clusters.setdefault(sb.get_id(), []).append(o)
                self.__total_task_count += 1

        # Return dict of computed object clusters possibly randomized
        return {k: clusters[k] for k in random.sample(clusters.keys(), len(clusters))}, non_clustered_tasks

    def __initialize_rank_queues(self):
        """Populates every rank's deque with all initial clusters."""
        for r in self.ranks.values():
            rank_clusters, loose_tasks = self.__build_rank_clusters(r, False)
            self.rank_queues[r.get_id()] = deque(cluster for cluster in rank_clusters.values())
            self.rank_queues[r.get_id()].extend(o for o in loose_tasks)

    def __reset(self):
        """Resets the algorithm for repeated experiments."""
        # Initialize algorithm
        self.__task_count = 0
        self.__total_task_count = 0
        self.__steal_count = 0
        self.__attempted_steal_count = 0
        ranks_list = self._rebalanced_phase.get_ranks()
        self.ranks = {rank.get_id(): rank for rank in ranks_list}
        self.num_ranks = len(self.ranks)
        self.__initialize_rank_queues()

    def __has_stealable_cluster(self, rank):
        """Asserts that a given rank has a stealable cluster."""
        stealable = False
        # Make sure rank is not empty
        if self.has_work(rank):

            # Make sure the last item in the queue is a cluster
            if isinstance(self.rank_queues[rank.get_id()][-1], list):

                # Make sure that the rank will not then be empty (prevent stealing back and forth)
                if len(self.rank_queues[rank.get_id()]) > 1:
                    stealable = True

        return stealable

    def respond_to_steal_request(self, steal_request: StealRequest):
        '''Resolves steal requests; if there is a cluster at the back of the receiving rank's queue, it is relocated to the sending rank's queue.'''
        # Get both ranks
        self.__attempted_steal_count += 1
        r_requesting = steal_request.get_requesting_rank()
        r_target = steal_request.get_target_rank()

        # Check that r_target has a cluster to steal
        if self.__has_stealable_cluster(r_target):

            # Perform steal
            cluster = self.rank_queues[r_target.get_id()].pop()
            print(f"Performing steal of shared block {cluster[0].get_shared_block_id()} (from {r_target.get_id()} to {r_requesting.get_id()})")
            self.rank_queues[r_requesting.get_id()].append(cluster)
            self.__steal_count += 1

    def get_task_count(self):
        """Returns number of tasks that have been simulated."""
        return self.__task_count

    def increment_task_count(self):
        """Increments the number of tasks that have been simulated."""
        self.__task_count += 1

    def get_total_task_count(self):
        """Returns the total number of tasks that need to be simualted."""
        return self.__total_task_count

    def has_work(self, rank):
        """Determines if a given rank has an object or cluster in its deque."""
        return any(isinstance(item, (Object, list)) for item in self.rank_queues[rank.get_id()])

    def any_ranks_have_work(self):
        """Determines if any rank has an object, cluster, or StealRequest in its deque."""
        return any(self.has_work(r) for r in self.ranks.values())

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """Performs the simulation and returns the average time to complete all tasks."""
        # Use initalize from AlgorithmBase
        self._initialize(p_id, phases, distributions, statistics)

        # Save time for every experiment
        experiment_times = []

        # Run over multiple experiments
        for exp in range(self.__num_experiments):

            # Print out current experiment
            self.__logger.info(f"Experiment {exp}")

            # Set up problem
            random.seed()
            workers = []

            # Create simpy environment
            env = simpy.Environment()

            # Instantiate RankWorkers
            for i in range(self.num_ranks):
                workers.append(RankWorker(env, i, self, self.__logger))

            # Run the environment
            env.run()

            # Report elapsed time and steals
            end_time = env.now
            self.__logger.info(f"  simulation finished at time {end_time}")
            self.__logger.info(f"  {self.__steal_count} steals ({self.__attempted_steal_count} attempted).")
            experiment_times.append(end_time)

            # Reset algorithm (re-initialize counts and queues)
            self.__reset()

        # Report average time for all experiments
        self.__logger.info(f"Average time: {sum(experiment_times)/len(experiment_times)}")
