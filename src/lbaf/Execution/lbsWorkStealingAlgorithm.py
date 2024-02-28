import sys
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
        """Creates a steal request in which r_snd attempts to steals a cluster from r_rcv."""
        self.__r_snd = r_snd
        self.__r_rcv = r_rcv

    def get_requesting_rank(self):
        """Returns the rank that requested a steal."""
        return self.__r_snd

    def get_target_rank(self):
        """Returns the rank targeted by the steal."""
        return self.__r_rcv


class RankWorker:
    def __init__(self, env, rank_id, algorithm, lgr: Logger):
        """Class that handles all steals and executions of tasks on a rank."""
        # Set up simpy environment
        self.env = env
        self.action = env.process(self.run())

        # Initialize logger and algorithm
        self.__logger = lgr
        self.algorithm = algorithm

        # Initialize rank information
        self.rank_id = rank_id
        self.rank = self.algorithm.ranks[self.rank_id]
        self.pending_steal_request = False
        self.other_ranks = [r_id for r_id in self.algorithm.ranks.keys() if r_id != self.rank_id]
        self.running = True

        # Initialize memory
        self.rank_memory = self.rank.get_size()

        # Initialize current cluster (if a rank is currently working through a cluster)
        self.current_cluster = None
        self.new_clusters = False

        # Output initial information
        self.__logger.info(f"  Rank {self.rank_id} Initial Info: work={self.__get_total_work()}, memory={self.rank_memory}, n_tasks={self.rank.get_number_of_objects()}, n_clusters={self.rank.get_number_of_shared_blocks()}")

    def run(self):
        """Defines the process that will run within the simpy environment."""
        # Continue if the rank has work and memory left
        while self.__continue_condition():

            # Print current clusters memories
            # cluster_size_list = []
            # for cluster in self.algorithm.rank_queues[self.rank_id]:
            #     if isinstance(cluster, list):
            #         cluster_size_list.append(self.algorithm.calculate_cluster_memory_footprint(cluster))
            # if len(cluster_size_list) > 0:
            #     print(f"Rank {self.rank_id}: {cluster_size_list}")

            # Check if rank has a cluster lined up
            if self.current_cluster is not None:

                # Execute all tasks on the cluster
                self.rank_memory += self.current_cluster[0].get_shared_block().get_size()
                for task in self.current_cluster:
                    yield self.env.process(self.__simulate_task(task))

                    # After each task, check if there is a steal request (to prevent hang ups)
                    if self.algorithm.do_stealing:
                        self.__check_for_steal_requests()

                # Once all tasks are executed, reset the current cluster
                self.current_cluster = None

                # TODO: how long?
                yield self.env.timeout(self.algorithm.steal_time)

            # Check for a StealRequest at the back of the queue
            elif self.algorithm.has_steal_request_at_back_of_deque(self.rank):
                steal_request = self.algorithm.rank_queues[self.rank_id].pop()
                self.algorithm.respond_to_steal_request(steal_request)
                yield self.env.timeout(self.algorithm.steal_time)

            # Check for work in queue
            elif self.algorithm.has_work_in_deque(self.rank, including_steals=True):

                # Pop next object in queue
                item = self.algorithm.rank_queues[self.rank_id].popleft()

                # If item is a cluster, try to move to self.current_cluster (will be executed next)
                if isinstance(item, list):

                    # Make sure there is memory on the rank to execute the cluster
                    if self.algorithm.rank_has_memory_for_cluster(self.rank, item):
                        self.current_cluster = item

                    # Otherwise, move to self.algorithm.memory_intensive_clusters so other ranks can "steal"
                    else:
                        if self.algorithm.do_stealing:
                            print(f"Rank {self.rank_id} (memory: {self.rank_memory}) moving cluster ({item[0].get_shared_block().get_size()}) to memory intensive clusters")
                            self.algorithm.memory_intensive_clusters.append(item)

                            # Then reset all other workers' new_clusters flag
                            for r_id in self.other_ranks:
                                self.algorithm.workers[r_id].new_clusters = True

                        # If steals are off, exit here
                        else:
                            sys.exit(f"Rank {self.rank_id} could not execute all tasks within the memory limit ({self.algorithm.max_memory_usage})")

                    yield self.env.timeout(0.01)

                # Catch any other datatypes
                else:
                    self.__logger.error(f"Received some other datatype: {type(item)}")

            # If no work is available, try to request a steal (either from a random rank or the memory intensive bank)
            elif self.algorithm.do_stealing and not self.pending_steal_request:

                # Check for new memory_intensive clusters
                num_intensive_clusters = len(self.algorithm.memory_intensive_clusters)
                if num_intensive_clusters > 0 and self.new_clusters:
                    idx = 0
                    for i in range(num_intensive_clusters):
                        cluster = self.algorithm.memory_intensive_clusters.pop(i)
                        if self.algorithm.rank_has_memory_for_cluster(self.rank, cluster):
                            self.current_cluster = cluster
                            break
                        else:
                            self.algorithm.memory_intensive_clusters.insert(i, cluster)
                            idx += 1

                    # Set new_clusters flag to false if we looped through all available clusters
                    self.new_clusters = False if idx == num_intensive_clusters else True

                    yield self.env.timeout(self.algorithm.steal_time) # TODO: is this right?

                # If no work is publicly available, steal from a random rank
                else:
                    target_rank_id = random.choice(self.other_ranks)
                    requesting_rank = self.rank
                    target_rank = self.algorithm.ranks[target_rank_id]
                    if self.algorithm.has_stealable_cluster(target_rank, requesting_rank):
                        self.algorithm.iterate_attempted_steals()
                        steal_request = StealRequest(requesting_rank, target_rank)
                        # Place steal request in target's queue
                        idx = self.algorithm.get_index_of_first_non_steal_request(target_rank)
                        self.algorithm.rank_queues[target_rank_id].insert(idx + 1, steal_request)
                        self.pending_steal_request = True
                        yield self.env.timeout(self.algorithm.steal_time) # TODO: are we double counting steal time here? (see line 99)
                    else:
                        yield self.env.timeout(0.01)

            else:
                # this rank is awaiting the fulfillment of a steal request
                # and can not proceed until it gets a response
                yield self.env.timeout(0.01) # TODO: need to yield here -- but for how long?

    def __continue_condition(self):
        """Continue if the rank has clusters in its queue. If stealing is on, also continue if any stealable clusters are available."""
        # Determine continuing condition
        if self.algorithm.do_stealing:
            available_work = self.__has_work() or self.algorithm.any_ranks_have_stealable_work(self.rank)
        else:
            available_work = self.__has_work()
        continue_condition = self.__has_memory() and available_work

        # Check if all ranks are done
        if not continue_condition:
            self.running = False
            # print(f"Rank {self.rank_id} is done running (memory {self.rank_memory}).")
        any_worker_still_running = any(worker.running for worker in self.algorithm.workers)

        # Throw error if all ranks are done but there is still work
        if not any_worker_still_running and len(self.algorithm.memory_intensive_clusters) > 0:
            sys.exit("lbsWorkStealingAlgorithm ran out of rank memory to execute all clusters. Consider increasing the max_memory_usage parameter.")

        # Otherwise, return the continue condition
        return continue_condition

    def __get_total_work(self):
        """Returns the total work on the rank."""
        total_work = 0.
        for item in self.algorithm.rank_queues[self.rank_id]:
            if isinstance(item, list):
                for o in item:
                    total_work += o.get_load()
        return total_work

    def __has_work(self):
        """Returns True if the rank has a cluster either in its queue or in its current_cluster member."""
        return self.algorithm.has_work_in_deque(self.rank) or self.current_cluster is not None

    def __has_memory(self):
        """Returns True if the rank is still below the maximum memory threshold."""
        return self.rank_memory < self.algorithm.max_memory_usage

    def __check_for_steal_requests(self):
        """Checks item at the back of the queue; if it's a steal request, responds accordingly."""
        rank_queue = self.algorithm.rank_queues[self.rank_id]
        if len(rank_queue) > 0 and isinstance(rank_queue[-1], StealRequest):
            steal_request = rank_queue.pop()
            self.algorithm.respond_to_steal_request(steal_request)
            yield self.env.timeout((self.algorithm.steal_time))

    def __simulate_task(self, task: Object):
        """Simulates the execution of a task."""
        self.algorithm.increment_task_count()
        self.rank_memory += task.get_size()
        num_steal_reqs = []
        # queue_sizes = []
        # for i in range(self.algorithm.num_ranks):
        #     queue_sizes.append(sum(isinstance(elm, list) for elm in self.algorithm.rank_queues[i]))
        #     num_steal_reqs.append(sum(isinstance(elm, StealRequest) for elm in self.algorithm.rank_queues[i]))
        task_time = task.get_load()
        # self.__logger.info(f"    Rank {self.rank_id}: executing task {task.get_id()} (sb_id {task.get_shared_block_id()}, load {task_time}) at time {self.env.now} ({self.algorithm.get_task_count()}/{self.algorithm.get_total_task_count()}) queue sizes={queue_sizes} steal requests = {num_steal_reqs}")
        self.__logger.info(f"    Rank {self.rank_id}: executing task {task.get_id()} (sb_id {task.get_shared_block_id()}, load {task_time}) at time {self.env.now} ({self.algorithm.get_task_count()}/{self.algorithm.get_total_task_count()}); memory: {self.rank_memory}/{self.algorithm.max_memory_usage}")
        yield self.env.timeout(task_time)


#################################################
#########        Algorithm class        #########
#################################################


class WorkStealingAlgorithm(AlgorithmBase):
    """
    A class for simulating work stealing for memory-constrained problems.
    Inherits from AlgorithmBase in order to fit in with LBAF's runtime, but many parameters go unused.
    """
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

        # Initialize the configuration parameters
        self.__discretion_interval = parameters.get("discretion_interval") # TODO: still necessary?
        self.steal_time = parameters.get("steal_time", 0.1)
        self.do_stealing = parameters.get("do_stealing", True)
        self.max_memory_usage = parameters.get("max_memory_usage", 8.0e+9)
        self.sort_clusters = parameters.get("sort_clusters", True)

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


    def __build_rank_clusters(self, rank: Rank) -> dict:
        """Cluster migratable objects by shared block ID when available."""
        # Iterate over all migratable objects on rank
        clusters = {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID
            sb = o.get_shared_block()
            # Add current object to its block ID cluster
            clusters.setdefault(sb.get_id(), []).append(o)
            self.__total_task_count += 1

        # Return randomized dict of computed object clusters
        return {k: clusters[k] for k in random.sample(clusters.keys(), len(clusters))}

    def __initialize_rank_queues(self):
        """Populates every rank's deque with all initial clusters."""
        for r in self.ranks.values():
            rank_clusters = self.__build_rank_clusters(r)
            if self.sort_clusters:
                clusters = sorted(rank_clusters.values(), key=self.calculate_cluster_memory_footprint, reverse=True)
            else:
                clusters = [cluster for cluster in rank_clusters.values()]
            self.rank_queues[r.get_id()] = deque(clusters)

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
        self.memory_intensive_clusters = []
        self.workers = []


    def calculate_cluster_memory_footprint(self, cluster):
        """Returns the total memory footprint of a given cluster."""
        cluster_size = cluster[0].get_shared_block().get_size()
        for task in cluster:
            cluster_size += task.get_size()
        return cluster_size

    def rank_has_memory_for_cluster(self, rank, cluster):
        """Returns True if the rank has enough memory to execute the cluster."""
        rank_memory = self.workers[rank.get_id()].rank_memory
        cluster_memory = self.calculate_cluster_memory_footprint(cluster)
        return rank_memory + cluster_memory < self.max_memory_usage

    def has_work_in_deque(self, rank, including_steals=False):
        """Determines if a given rank's deque has a cluster (or StealRequest, if including_steals is True)."""
        if including_steals:
            return any(isinstance(item, (list, StealRequest)) for item in self.rank_queues[rank.get_id()])
        else:
            return any(isinstance(item, list) for item in self.rank_queues[rank.get_id()])

    def has_steal_request_at_back_of_deque(self, rank):
        """Determines if a given rank's deque has a StealRequest at the back."""
        return self.has_work_in_deque(rank, including_steals=True) and isinstance(self.rank_queues[rank.get_id()][-1], StealRequest)

    def get_task_count(self):
        """Returns number of tasks that have been simulated."""
        return self.__task_count

    def increment_task_count(self):
        """Increments the number of tasks that have been simulated."""
        self.__task_count += 1

    def get_total_task_count(self):
        """Returns the total number of tasks that need to be simualted."""
        return self.__total_task_count

    def get_index_of_first_non_steal_request(self, rank):
        """Returns the index of the first non-StealRequest in a rank's deque (iterating from the back)."""
        rank_queue = self.rank_queues[rank.get_id()]
        for i in range(len(rank_queue) - 1, -1, -1):
            if not isinstance(rank_queue[i], StealRequest):
                return i

    def iterate_attempted_steals(self):
        """Increases number of attempted steals by one."""
        self.__attempted_steal_count += 1

    def has_stealable_cluster(self, target_rank, requesting_rank):
        """Asserts that a given target_rank has a stealable cluster at the front of its deque.
        Also checks that the requesting rank has enough memory for the steal."""
        rank_queue = self.rank_queues[target_rank.get_id()]

        # Make sure target_rank has a cluster at the back of its queue
        has_cluster = self.has_work_in_deque(target_rank) and isinstance(rank_queue[0], list)

        # Make sure the requesting rank has enough memory to execute the cluster
        return has_cluster and self.rank_has_memory_for_cluster(requesting_rank, rank_queue[0])

    def respond_to_steal_request(self, steal_request: StealRequest):
        """Resolves steal requests; if there is a cluster at the front of the receiving rank's queue, it is relocated to the sending rank's queue."""
        # Get both ranks
        r_requesting = steal_request.get_requesting_rank()
        r_target = steal_request.get_target_rank()

        # Double check that r_target still has a cluster to steal
        if self.has_stealable_cluster(r_target, r_requesting):

            # Perform steal
            cluster = self.rank_queues[r_target.get_id()].popleft()
            self.__logger.info(f"    Performing steal of shared block {cluster[0].get_shared_block_id()} (from {r_target.get_id()} to {r_requesting.get_id()})")
            self.rank_queues[r_requesting.get_id()].appendleft(cluster)
            self.__steal_count += 1

        else:
            self.__logger.info(f"    Rank {r_target.get_id()} has no stealable clusters for {r_requesting.get_id()}")

        # set false as we are responding, either by putting work or doing nothing
        self.workers[r_requesting.get_id()].pending_steal_request = False

    def any_ranks_have_stealable_work(self, requesting_rank):
        """Determines if any rank has a cluster in its deque that can be stolen by requesting_rank."""
        return any(self.has_stealable_cluster(r, requesting_rank) for r in self.ranks.values())

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """Performs the simulation and returns the average time to complete all tasks."""
        # Use initalize from AlgorithmBase
        self._initialize(p_id, phases, distributions, statistics)

        # Save time for every experiment
        experiment_times = []

        # Run over multiple experiments
        for exp in range(self.__num_experiments):

            # Reset algorithm (re-initialize counts and queues)
            self.__reset()

            # Print out current experiment
            self.__logger.info(f"Experiment {exp} ({self.get_total_task_count()} tasks)")

            # Set up problem
            random.seed()

            # Create simpy environment
            env = simpy.Environment()

            # Instantiate RankWorkers
            for i in range(self.num_ranks):
                self.workers.append(RankWorker(env, i, self, self.__logger))

            # Run the environment
            env.run()

            # Report elapsed time and steals
            end_time = env.now
            self.__logger.info(f"  simulation finished at time {end_time} ({self.__steal_count}/{self.__attempted_steal_count} steals completed)")
            experiment_times.append(end_time)

        # Report average time for all experiments
        self.__logger.info(f"Average time: {sum(experiment_times)/len(experiment_times):0.2f}")
