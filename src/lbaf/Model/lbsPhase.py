import random as rnd
from logging import Logger
from typing import Optional

from ..IO.lbsStatistics import print_function_statistics, print_subset_statistics, sampler
from ..IO.lbsVTDataReader import LoadReader
from ..Utils.lbsLogging import get_logger
from .lbsBlock import Block
from .lbsObject import Object
from .lbsObjectCommunicator import ObjectCommunicator
from .lbsRank import Rank


class Phase:
    """A class representing a phase of objects distributed across ranks."""

    def __init__(
        self,
        lgr: Logger,
        p_id: int = 0,
        reader: LoadReader = None):
        """Class constructor
            logger: a Logger instance
            id: an integer indexing the phase ID
            reader: a JSON VT reader instance"""
        # Assert that a logger instance was passed
        if not isinstance(lgr, Logger):
            get_logger().error(
                f"Incorrect type {type(lgr)} passed instead of Logger instance")
            raise SystemExit(1)
        self.__logger = lgr
        self.__logger.info(f"Instantiating phase {p_id}")

        # Index of this phase
        self.__phase_id = p_id

        # Initialize empty list of ranks
        self.__ranks = []

        # Start with null set of edges
        self.__edges = None

        # VT Data Reader
        self.__reader = reader

    def set_id(self, p_id: int):
        """ Set index of this phase."""
        self.__phase_id = p_id

    def get_id(self):
        """Retrieve index of this phase."""
        return self.__phase_id

    def get_number_of_ranks(self):
        """Retrieve number of ranks belonging to phase."""
        return len(self.__ranks)

    def set_ranks(self, ranks: list):
        """ Set list of ranks for this phase."""
        self.__ranks = ranks

    def get_ranks(self):
        """Retrieve ranks belonging to phase."""

        return self.__ranks

    def get_rank_ids(self):
        """Retrieve IDs of ranks belonging to phase."""
        return [p.get_id() for p in self.__ranks]

    def get_number_of_objects(self):
        """Return number of objects."""
        return sum([r.get_number_of_objects() for r in self.__ranks])

    def get_objects(self):
        """Return all objects belonging to phase."""
        # List comprehension is not possible as we need to use set to list concatenation
        objects = []
        for rank in self.__ranks:
            objects += rank.get_objects()
        objects.sort(key=lambda x: x.get_id())
        return objects

    def get_objects_dict(self):
        """Return all objects as dictionaries with `from` and `to` values retrieved from the object communicator."""
        objects = []
        for o in self.get_objects():
            entry = {
                "id": o.get_id(),
                "rank": o.get_rank_id(),
                "load": o.get_load(),
                "to": {},
                "from": {}}
            comm = o.get_communicator()
            if comm:
                for k, v in comm.get_sent().items():
                    entry["to"][k.get_id()] = v
                for k, v in comm.get_received().items():
                    entry["from"][k.get_id()] = v
            objects.append(entry)
        objects.sort(key=lambda x: x.get("id"))
        return objects

    def get_object_ids(self):
        """Return IDs of all objects belonging to phase."""
        # List comprehension is not possible as we need to use set to list concatenation
        ids = []
        for r in self.__ranks:
            ids += r.get_object_ids()
        return ids

    def compute_edges(self):
        """Compute and return dict of communication edge IDs to volumes."""
        # Compute or re-compute edges from scratch
        self.__logger.info("Computing inter-rank communication edges")
        self.__edges = {}

        # Initialize sum of total and rank-local volumes
        v_total, v_local = 0., 0.

        # Iterate over ranks
        for rank in self.__ranks:
            # Retrieve sender rank ID
            i = rank.get_id()
            self.__logger.debug(f"rank {i}:")

            # Iterate over objects of current rank
            for o in rank.get_objects():
                self.__logger.debug(f"* object {o.get_id()}:")

                # Iterate over recipient objects
                for sent, volume in o.get_sent().items():
                    # Update total volume
                    v_total += volume

                    # Retrieve recipient rank ID
                    j = sent.get_rank_id()
                    self.__logger.debug(f"sent volume {volume} to object {sent.get_id()} assigned to rank {j}")

                    # Skip rank-local communications
                    if i == j:
                        # Update sum of local volumes and continue
                        v_local += volume
                        continue

                    # Create or update an inter-rank directed edge
                    ij = frozenset([i, j])
                    self.__edges.setdefault(ij, [0., 0.])
                    if i < j :
                        self.__edges[ij][0] += volume
                    else:
                        self.__edges[ij][1] += volume
                    self.__logger.debug(f"edge rank {i} --> rank {j}, volume: {self.__edges[ij]}")

        # Report on computed edges
        n_ranks = len(self.__ranks)
        n_edges = len(self.__edges)
        print_subset_statistics(
            "Inter-rank communication edges",
            n_edges,
            "possible ones",
            n_ranks * (n_ranks - 1) / 2,
            self.__logger)
        print_subset_statistics(
            "Rank-local communication volume",
            v_local,
            "total volume",
            v_total, self.__logger)

    def get_edges(self):
        """Retrieve communication edges of phase. """
        # Compute edges when not available
        if self.__edges is None:
            self.compute_edges()

        # Return edges
        return self.__edges

    def get_edge_maxima(self):
        """Reduce directed edges into undirected with maximum."""
        # Compute edges when not available
        if self.__edges is None:
            self.compute_edges()

        # Return edge with maximum volume
        return {k: max(v) for k, v in self.__edges.items()}

    def get_largest_volumes(self):
        """Return largest directed volumes from undirected ones."""
        # Compute edges when not available
        if self.__edges is None:
            self.compute_edges()

        # Return maximum values at edges
        return [max(v) for v in self.__edges.values()]

    def __update_or_create_directed_edge(self, from_id: int, to_id: int, v: float):
        """Convenience method to update or create directed edge with given volume."""
        # Create undidrected edge index and try to retrieve edge
        e_id = frozenset([from_id, to_id])
        edge = self.__edges.get(e_id)

        # Update or create edge
        if edge is None:
            # Edge must be created
            self.__logger.debug(
                f"Creating edge {from_id} --> {to_id} with volume {v}")
            self.__edges[e_id] = [0.0, 0.0]
            self.__edges[e_id][0 if from_id < to_id else 1] = v
        else:
            # Edge can be updated
            self.__logger.debug(
                f"Updating edge {from_id} --> {to_id} with volume {v}")
            edge[0 if from_id < to_id else 1] += v

        # Eliminate edge if communication vanished in both directions
        if edge == [0.0, 0.0]:
            self.__logger.debug(
                f"Eliminating {from_id}--{to_id} edge as its communications vanished both ways")
            del self.__edges[e_id]

    def update_edges(self, o: Object, r_src: Rank, r_dst: Rank):
        """Update inter-rank communication edges before object transfer."""
        # Compute edges when not available
        if self.__edges is None:
            self.compute_edges()
            return

        # Break out early when object has no communicator
        comm = o.get_communicator()
        if not isinstance(comm, ObjectCommunicator):
            self.__logger.debug(f"Object {o.get_id()} does not have a communicator, cannot update edges")
            return

        # Keep track of indices related to src and dst
        src_id, dst_id = r_src.get_id(), r_dst.get_id()
        self.__logger.debug(
            f"Transferring object {o.get_id()} from {src_id} to {dst_id}")

        # Tally sent communication volumes by destination
        for k, v in comm.get_sent().items():
            # Distinguish between possible cases for other communication endpoint
            oth_id = k.get_rank_id()
            self.__logger.debug(
                f"\tvolume {v} {src_id} --> {oth_id} becomes {dst_id} --> {oth_id}")
            if oth_id  == src_id:
                # Local src communication becomes off-node dst to src
                self.__update_or_create_directed_edge(dst_id, src_id, +v)
            elif oth_id == dst_id:
                # Off-node src to dst communication becomes dst local
                self.__update_or_create_directed_edge(src_id, dst_id, -v)
            else:
                # Off-node src to oth communication becomes dst to oth
                self.__update_or_create_directed_edge(src_id, oth_id, -v)
                self.__update_or_create_directed_edge(dst_id, oth_id, +v)

        # Tally received communication volumes by source
        for k, v in comm.get_received().items():
            # Distinguish between possible cases for other communication endpoint
            oth_id = k.get_rank_id()
            self.__logger.debug(
                f"\tvolume {v} on {src_id} <-- {oth_id} becomes {dst_id} <-- {oth_id}")
            if oth_id == src_id:
                # Local src communication becomes off-node dst from src
                self.__update_or_create_directed_edge(src_id, dst_id, +v)
            elif oth_id == dst_id:
                # Off-node src from dst communication becomes dst local
                self.__update_or_create_directed_edge(dst_id, src_id, -v)
            else:
                # Off-node src from oth communication becomes dst from oth
                self.__update_or_create_directed_edge(oth_id, src_id, -v)
                self.__update_or_create_directed_edge(oth_id, dst_id, +v)

    def populate_from_samplers(self, n_ranks, n_objects, t_sampler, v_sampler, c_degree, n_r_mapped=0):
        """Use samplers to populate either all or n ranks in a phase."""

        # Retrieve desired load sampler with its theoretical average
        load_sampler, sampler_name = sampler(t_sampler.get("name"), t_sampler.get("parameters"), self.__logger)

        # Create n_objects objects with uniformly distributed loads in given range
        self.__logger.info(
            f"Creating {n_objects} objects with loads sampled from {sampler_name}")
        objects = set([
            Object(i, load=load_sampler())
            for i in range(n_objects)])

        # Compute and report object load statistics
        print_function_statistics(
            objects, lambda x: x.get_load(), "object loads", self.__logger)

        # Decide whether communications must be created
        if c_degree > 0:
            # Instantiate communication samplers with requested properties
            volume_sampler, volume_sampler_name = sampler(
                v_sampler.get("name"),
                v_sampler.get("parameters"), self.__logger)

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
                    s={o: volume_sampler() for o in rnd.sample(
                        objects.difference([obj]), degree_sampler())},
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
            self.__logger.error(
                f"Number of sent and received communications differ: {len(v_sent)} <> {len(v_recv)}")
            raise SystemExit(1)

        # Compute and report communication volume statistics
        print_function_statistics(v_sent, lambda x: x, "communication volumes", self.__logger)

        # Create given number of ranks
        self.__ranks = [Rank(self.__logger, r_id) for r_id in range(n_ranks)]

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

    def populate_from_log(self, phase_id):
        """Populate this phase by reading in a load profile from log files."""
        # Populate phase with JSON reader output
        self.__ranks = self.__reader.populate_phase(phase_id)
        objects = set()
        for p in self.__ranks:
            objects = objects.union(p.get_objects())

        # Compute and report object statistics
        print_function_statistics(
            objects, lambda x: x.get_load(), "object loads", self.__logger)
        print_function_statistics(
            objects, lambda x: x.get_size(), "object sizes", self.__logger)
        print_function_statistics(
            objects, lambda x: x.get_overhead(), "object overheads", self.__logger)

    def transfer_object(self, r_src: Rank, o: Object, r_dst: Rank):
        """Transfer object from source to destination rank."""

        # Keep track of object ID for convenience
        o_id = o.get_id()

        # Log info in debug mode
        self.__logger.debug(
            f"Transferring object {o_id} from rank {r_src.get_id()} to {r_dst.get_id()}")

        # Update inter-rank edges before moving objects
        self.update_edges(o, r_src, r_dst)

        # Remove object from migratable ones on source
        r_src.remove_migratable_object(o, r_dst)

        # Add object to migratable ones on destination
        r_dst.add_migratable_object(o)

        # Reset current rank of object
        o.set_rank_id(r_dst.get_id())

        # Update shared blocks when needed
        if (block := o.get_shared_block()):
            # Detach object from block on source and clean up as needed
            b_id = block.get_id()
            self.__logger.debug(
                f"Removing object {o_id} attachment to block {b_id} on rank {r_src.get_id()}")

            # Perform sanity check
            if b_id not in r_src.get_shared_block_ids():
                self.__logger.error(
                f"block {b_id} not present on in {r_src.get_shared_blocks()}")
                raise SystemExit(1)

            if not block.detach_object_id(o_id):
                # Delete shared block if no tied object left on rank
                r_src.delete_shared_block(block)

            # Replicate or update block on destination rank
            if not (b_dst := r_dst.get_shared_block_with_id(b_id)):
                # Replicate block when not present on destination rank
                self.__logger.debug(
                    f"Replicating block {b_id} onto rank {r_dst.get_id()}")
                r_dst.add_shared_block(b_dst := Block(
                    b_id, block.get_home_id(), block.get_size(), {o_id}))
            else:
                # Update block when present on destination rank
                self.__logger.debug(
                    f"Block {b_id} already present on rank {r_dst.get_id()}")

            # Attach object to block on destination rank
            b_dst.attach_object_id(o_id)
            o.set_shared_block(b_dst)

    def transfer_objects(self, r_src: Rank, o_src: list, r_dst: Rank, o_dst: Optional[list] = None):
        """Transfer list of objects between source and destination ranks."""

        if not o_dst:
            o_dst = []

        # Transfer objects from source to destination
        for o in o_src:
            self.transfer_object(r_src, o, r_dst)
        n_transfers = len(o_src)
        self.__logger.debug(
            f"Transferred {n_transfers} objects from rank {r_src.get_id()} to {r_dst.get_id()}")

        # Transfer objects back from destination to source
        for o in o_dst:
            self.transfer_object(r_dst, o, r_src) # pylint:disable=W1114:arguments-out-of-order
        n_transfers += (n_reverse := len(o_dst))
        if n_reverse:
            self.__logger.debug(
                f"Transferred back {n_transfers} objects from rank {r_dst.get_id()} to {r_src.get_id()}")

        # Return number of transferred objects
        return n_transfers
