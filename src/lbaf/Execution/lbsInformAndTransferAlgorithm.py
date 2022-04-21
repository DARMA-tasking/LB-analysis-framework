from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics

class InformAndTransferAlgorithm(AlgorithmBase):
    """ A concrete class for the 2-phase gossip+transfer algorithm
    """

    def __init__(self, work_model, parameters: dict = None, lgr: Logger = None):
        """ Class constructor
            work_model: WorkModelBase instance
            parameters: optional parameters dictionary
        """


        # Call superclass init
        super(InformAndTransferAlgorithm, self).__init__(work_model, parameters)

        # Assign logger to instance variable
        self.__logger = lgr
        self.__logger.info(f"Instantiated {type(self).__name__} concrete algorithm")

    def information_stage(self, n_rounds, f):
        """ Execute information phase
            n_rounds: integer number of gossiping rounds
            f: integer fanout
        """

        # Build set of all ranks in the phase
        rank_set = set(self.__phase.get_ranks())

        # Initialize gossip process
        self.__logger.info(f"Initializing information messages with fanout = {f}")
        gossip_round = 1
        gossips = {}

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_message(rank_set, f)
            for p_rcv in dst:
                gossips.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in gossips.items():
            for m in msg_lst:
                p_rcv.process_message(m)

        # Report on gossiping status when requested
        for p in rank_set:
            self.__logger.debug(f"information known to rank {p.get_id()}: {[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Forward messages for as long as necessary and requested
        while gossip_round < n_rounds:
            # Initiate next gossiping round
            self.__logger.debug(f"Performing message forwarding round {gossip_round}")
            gossip_round += 1
            gossips.clear()

            # Iterate over all ranks
            for p_snd in rank_set:
                # Check whether rank must relay previously received message
                if p_snd.round_last_received + 1 == gossip_round:
                    # Collect message when destination list is not empty
                    dst, msg = p_snd.forward_message(gossip_round, rank_set, f)
                    for p_rcv in dst:
                        gossips.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in gossips.items():
                for m in msg_lst:
                    p_rcv.process_message(m)

            # Report on gossiping status when requested
            for p in rank_set:
                self.__logger.debug(f"information known to rank {p.get_id()}: "
                               f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Build reverse lookup of ranks to those aware of them
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

            # Update viewers on loaded ranks known to this one
            p.add_as_viewer(p.get_known_loads().keys())

        # Report on viewers of loaded ranks
        viewers_counts = {}
        for p in rank_set:
            # Skip non loaded ranks
            if not p.get_load():
                continue

            # Retrieve cardinality of viewers
            viewers = p.get_viewers()
            viewers_counts[p] = len(viewers)

            # Report on viewers of loaded rank when requested
            self.__logger.debug(f"viewers of rank {p.get_id()}: {[p_o.get_id() for p_o in viewers]}")

        # Report viewers counts to loaded ranks
        self.__logger.info(f"Completed {n_rounds} information rounds")
        n_v, v_min, v_ave, v_max, _, _, _, _ = compute_function_statistics(viewers_counts.values(), lambda x: x)
        self.__logger.info(f"Reporting viewers counts (min:{v_min}, mean: {v_ave:.3g} max: {v_max}) to {n_v} loaded ranks")

    def recursive_extended_search(self, pick_list, object_list, c_fct, n_o, max_n_o):
        """ Recursively extend search to other objects
        """
        # Fail when no more objects available or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        object_list.append(o)
        n_o += 1

        # Decide whether criterion allows for transfer
        if c_fct(object_list) < 0.:
            # Transfer is not possible, recurse further
            return self.recursive_extended_search(pick_list, object_list, c_fct, n_o, max_n_o)
        else:
            # Succeed when criterion is satisfied
            return True


    def execute(self, phase: Phase):
        """ Execute 2-phase gossip+transfer algorithm
        """

        # Report on initial per-rank work
        print_function_statistics(
            phase.get_ranks(),
            lambda x: self.__work_model.compute(x),
            "initial rank works",
            logger=self.__logger)
