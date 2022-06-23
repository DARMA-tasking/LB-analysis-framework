from logging import Logger
import random as rnd
import sys

from .lbsObject import Object
from .lbsRank import Rank
from .lbsObjectCommunicator import ObjectCommunicator

from ..IO.lbsStatistics import print_subset_statistics, print_function_statistics, sampler
from ..IO.lbsVTDataReader import LoadReader
from ..Utils.exception_handler import exc_handler


class Phase:
    """ A class representing the state of collection of ranks with objects at a given round
    """

    def __init__(self, logger: Logger, t: int = 0, file_suffix="json"):
        # Initialize empty list of ranks
        self.__ranks = []

        # Initialize null number of objects
        self.__n_objects = 0

        # Default time-step/phase of this phase
        self.__phase_id = t

        # Assign logger to instance variable
        self.__logger = logger

        # Start with empty edges cache
        self.__edges = {}
        self.__cached_edges = False

        # Data files suffix(reading from data)
        self.__file_suffix = file_suffix

    def get_number_of_ranks(self):
        """ Retrieve number of ranks belonging to phase."""
        return len(self.__ranks)

    def get_ranks(self):
        """ Retrieve ranks belonging to phase."""
        return self.__ranks

    def get_rank_ids(self):
        """ Retrieve IDs of ranks belonging to phase."""
        return [p.get_id() for p in self.__ranks]

    def get_phase_id(self):
        """ Retrieve the time-step/phase for this phase."""
        return self.__phase_id

    def get_number_of_objects(self):
        """ Return number of objects."""
        return self.__n_objects

    def get_object_ids(self):
        """ Return IDs of ranks belonging to phase."""
        ids = []
        for p in self.__ranks:
            ids += p.get_object_ids()
        return ids

    def compute_edges(self):
        """ Compute and return map of communication link IDs to volumes."""
        # Compute or re-compute edges from scratch
        self.__logger.debug("Computing inter-rank communication edges")
        self.__edges.clear()
        directed_edges = {}

        # Initialize count of loaded ranks
        n_loaded = 0

        # Initialize sum of total and rank-local volumes
        v_total, v_local = 0., 0.

        # Iterate over ranks
        for p in self.__ranks:
            # Retrieve sender rank ID
            i = p.get_id()
            self.__logger.debug(f"rank {i}:")

            # Iterate over objects of current rank
            for o in p.get_objects():
                self.__logger.debug(f"* object {o.get_id()}:")

                # Iterate over recipient objects
                for q, volume in o.get_sent().items():
                    # Update total volume
                    v_total += volume

                    # Retrieve recipient rank ID
                    j = q.get_rank_id()
                    self.__logger.debug(f"sent volume {volume} to object {q.get_id()} assigned to rank {j}")

                    # Skip rank-local communications
                    if i == j:
                        # Update sum of local volumes and continue
                        v_local += volume
                        continue

                    # Create or update an inter-rank directed edge
                    ij = frozenset([i, j])
                    directed_edges.setdefault(ij, [0., 0.])
                    if i < j :
                        directed_edges[ij][0] += volume
                    else:
                        directed_edges[ij][1] += volume
                    self.__logger.debug(f"edge rank {i} --> rank {j}, volume: {directed_edges[ij]}")

        # Reduce directed edges into undirected ones with maximum
        for k, v in directed_edges.items():
            self.__edges[k] = max(v)

        # Edges cache was fully updated
        self.__cached_edges = True

        # Report on computed edges
        n_ranks = len(self.__ranks)
        n_edges = len(self.__edges)
        print_subset_statistics("Inter-rank communication edges", n_edges, "possible ones", n_ranks * (n_ranks - 1) / 2,
                                self.__logger)
        print_subset_statistics("Rank-local communication volume", v_local, "total volume", v_total, self.__logger)

    def get_edges(self):
        """ Retrieve edges belonging to phase. """
        # Force recompute if edges cache is not current
        if not self.__cached_edges:
            self.compute_edges()

        # Return cached edges
        return self.__edges

    def invalidate_edge_cache(self):
        """ Mark cached edges as no longer current."""
        self.__cached_edges = False

    def populate_from_samplers(self, n_ranks, n_objects, t_sampler, v_sampler, c_degree, n_r_mapped=0):
        """ Use samplers to populate either all or n ranks in a phase."""
        # Retrieve desired time sampler with its theoretical average
        time_sampler, sampler_name = sampler(t_sampler.get("name"), t_sampler.get("parameters"), self.__logger)

        # Create n_objects objects with uniformly distributed times in given range
        self.__logger.info(f"Creating {n_objects} objects with times sampled from {sampler_name}")
        self.__number_of_objects = n_objects
        objects = set([Object(i, time_sampler()) for i in range(n_objects)])

        # Compute and report object time statistics
        print_function_statistics(objects, lambda x: x.get_time(), "object times", self.__logger)

        # Decide whether communications must be created
        if c_degree > 0:
            # Instantiate communication samplers with requested properties
            volume_sampler, volume_sampler_name = sampler(
                v_sampler.get("name"), v_sampler.get("parameters"), self.__logger)

            # Create symmetric binomial sampler capped by number of objects for degree
            p_b = .5
            degree_sampler, degree_sampler_name = sampler(
                "binomial", [min(n_objects - 1, int(c_degree / p_b)), p_b], self.__logger)
            self.__logger.info("Creating communications with:")
            self.__logger.info(f"\tvolumes sampled from {volume_sampler_name}")
            self.__logger.info(f"\tout-degrees sampled from {degree_sampler_name}")

            # Create communicator for each object with only sent communications
            for obj in objects:
                # Create object communicator with outgoing messages
                obj.set_communicator(ObjectCommunicator(
                    i=obj.get_id(),
                    logger=self.__logger,
                    r={},
                    s={o: volume_sampler() for o in rnd.sample(objects.difference([obj]), degree_sampler())},
                ))

            # Create symmetric received communications
            for obj in objects:
                for k, v in obj.get_communicator().get_sent().items():
                    k.get_communicator().get_received()[obj] = v

        # Iterate over all object communicators to valid global communication graph
        v_sent, v_recv = [], []
        for obj in objects:
            i = obj.get_id()
            self.__logger.debug(f"object {i}:")

            # Retrieve communicator and proceed to next object if empty
            comm = obj.get_communicator()
            if not comm:
                self.__logger.debug("None")
                continue

            # Check and summarize communications and update global counters
            v_out, v_in = comm.summarize()
            v_sent += v_out
            v_recv += v_in

        # Perform sanity checks
        if len(v_recv) != len(v_sent):
            self.__logger.error(f"Number of sent and received communications differ: {len(v_sent)} <> {len(v_recv)}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Compute and report communication volume statistics
        print_function_statistics(v_sent, lambda x: x, "communication volumes", self.__logger)

        # Create n_ranks ranks
        self.__ranks = [Rank(i, self.__logger) for i in range(n_ranks)]

        # Randomly assign objects to ranks
        if n_r_mapped and n_r_mapped <= n_ranks:
            self.__logger.info(f"Randomly assigning objects to {n_r_mapped} ranks amongst {n_ranks}")
        else:
            # Sanity check
            if n_r_mapped > n_ranks:
                self.__logger.warning(
                    f"Too many ranks ({n_r_mapped}) requested: only {n_ranks} available.")
                n_r_mapped = n_ranks
            self.__logger.info(f"Randomly assigning objects to {n_ranks} ranks")
        if n_r_mapped > 0:
            # Randomly assign objects to a subset o ranks of size n_r_mapped
            rank_list = rnd.sample(self.__ranks, n_r_mapped)
            for o in objects:
                p = rnd.choice(rank_list)
                p.add_migratable_object(o)
                o.set_rank_id(p.get_id())
        else:
            # Randomly assign objects to all ranks
            for o in objects:
                p = rnd.choice(self.__ranks)
                p.add_migratable_object(o)
                o.set_rank_id(p.get_id())

        # Print debug information when requested
        for p in self.__ranks:
            self.__logger.debug(f"{p.get_id()} <- {p.get_object_ids()}")

    def populate_from_log(self, n_ranks, t_s, basename):
        """ Populate this phase by reading in a load profile from log files."""
        # Instantiate VT load reader
        reader = LoadReader(basename, self.__logger, file_suffix=self.__file_suffix)

        # Populate phase with reader output
        self.__ranks = reader.read_iteration(n_ranks, t_s)

        # Compute and report object statistics
        objects = set()
        for p in self.__ranks:
            objects = objects.union(p.get_objects())
        print_function_statistics(objects, lambda x: x.get_time(), "object times", self.__logger)

        # Set number of read objects
        self.__n_objects = len(objects)
        self.__logger.info(f"Read {self.__n_objects} objects from time-step {t_s} of data files with prefix {basename}")
