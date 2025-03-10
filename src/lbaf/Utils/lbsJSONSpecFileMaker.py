import os
import yaml
from typing import Set, List, Union

from lbaf.Execution.lbsPhaseSpecification import (
    PhaseSpecification, SharedBlockSpecification,
    RankSpecification, TaskSpecification,
    PhaseSpecificationNormalizer
)

class JSONSpecFileMaker:

    ###########################################################################
    ## Constructor

    def __init__(self):
        self.tasks = {}
        self.ranks = {}
        self.comms = {}
        self.shared_blocks = {}

        self.assignments = {} # { task_id: rank_id }

        self.current_ids = {
            "seq": 0,
            "shared": 0,
            "rank": 0,
            "phase": 0,
        }

        self.id_sets = {
            "seq": set(),
            "shared": set(),
            "rank": set(),
            "phase": set(),
        }


    ###########################################################################
    ## Private generators

    def generateNextID_(self, key: str) -> int:
        """
        Generic function to generate and update the next available ID for a given category.
        """
        if key not in self.current_ids or key not in self.id_sets:
            raise ValueError(f"Invalid key: {key}")

        while self.current_ids[key] in self.id_sets[key]:
            self.current_ids[key] += 1

        next_id = self.current_ids[key]
        self.current_ids[key] += 1
        return next_id

    def checkID_(self, id: int, key: str) -> int:
        if id < 0:
            id = self.generateNextID_(key)
        elif id in self.id_sets[key]:
            return self.checkID_(-1, key)
        self.id_sets[key].add(id)
        return id

    ###########################################################################
    ## Private functions for assertions

    def assertIDExists_(self, test_id: int, id_type: str):
        assert test_id in self.id_sets[id_type], \
               f"Task {test_id} has not been created yet. Use createTask() method."

    def assertAllTasksHaveBeenAssigned_(self):
        for t in self.tasks.keys():
            assert t in self.assignments, \
                   f"Task {t} has not been assigned. Call " \
                   f"assignTask({t}, <rank_id>, <phase_id>)"



    ###########################################################################
    ## Public Functions for creating JSON fields

    def createTask(self,
            time: float,
            seq_id: int = -1,
            collection_id: int = 7,
            migratable: bool = True,
            home = -1,
            node = -1,
            user_defined: dict = None) -> TaskSpecification:
        seq_id = self.checkID_(seq_id, "seq")
        task = TaskSpecification({
            "time": time,
            "seq_id": seq_id,
            "collection_id": collection_id,
            "migratable": migratable,
            "home": home,
            "node": home if node == -1 else node,
        })
        if user_defined is not None:
            task["user_defined"] = user_defined
        self.tasks[seq_id] = task
        return task

    def createSharedBlock(self,
            bytes: float,
            tasks: Union[List[int], List[TaskSpecification]],
            rank_id: int = -1,
            id: int = -1):
        shared_id = self.checkID_(id, "shared")
        shared_block = SharedBlockSpecification({
            "size": bytes,
            "shared_id": shared_id,
        })
        if rank_id >= 0:
            shared_block["home_rank"] = rank_id
        # Option to assign tasks to shared block
        task_specs = {}
        if tasks is not None:
            for t in tasks:
                if isinstance(t, int):
                    task_specs[t] = self.tasks[t]
                elif isinstance(t, dict):
                    task_specs[t["seq_id"]] = t
                else:
                    raise RuntimeError(
                        f"tasks must be a list of ints (IDs) or TaskSpecifications")
        shared_block["tasks"] = task_specs
        self.shared_blocks[shared_id] = shared_block
        return shared_block

    def createRank(self,
            id: int = -1,
            tasks: Union[List[int], List[TaskSpecification]] = None,
            user_defined: dict = None
        ) -> RankSpecification:
        id = self.checkID_(id, "rank")
        rank = RankSpecification({
            "id": id
        })

        # Optionally add tasks to the rank
        t_set : Set[TaskSpecification] = set()
        if tasks is not None:
            for t in tasks:
                if isinstance(t, int):
                    t_set.add(t)
                elif isinstance(t, dict):
                    t_set.add(t["seq_id"])
                else:
                    raise RuntimeError(
                        f"Tasks must be either ints (seq_ids) or TaskSpecifications."
                    )
        rank["tasks"] = t_set

        # Optionally add user_defined info to the rank
        if user_defined is not None:
            rank["user_defined"] = user_defined

        self.ranks[id] = rank
        return rank

    def assignTask(self,
            task: Union[int, TaskSpecification],
            rank: Union[int, RankSpecification]
        ) -> None:
        task_id = task if isinstance(task, int) else task["seq_id"]
        t = task if isinstance(task, dict) else self.tasks[task_id]

        rank_id = rank if isinstance(rank, int) else rank["id"]
        r = rank if isinstance(rank, dict) else self.ranks[rank_id]

        self.assertIDExists_(task_id, "seq")
        self.assertIDExists_(rank_id, "rank")

        # Make assignments
        t["home"] = rank_id
        if t["node"] == -1:
            t["node"] = rank_id
        r["tasks"].add(task_id)

        # If the task belongs to a shared_block,
        # update the block's home rank as well
        for sb in self.shared_blocks.values():
            if "home_rank" not in sb and task_id in sb.get("tasks", []):
                sb["home_rank"] = rank_id

        # Keep track of assignment
        self.assignments[task_id] = rank_id


    ###########################################################################
    ## Standard Getters

    def getRank(self, id: int) -> RankSpecification:
        return self.ranks[id]

    def getTask(self, seq_id: int) -> TaskSpecification:
        return self.tasks[seq_id]

    def getSharedBlock(self, id: int) -> SharedBlockSpecification:
        return self.shared_blocks[id]

    ###########################################################################
    ## Writer

    def write(self, path: str = None):
        self.assertAllTasksHaveBeenAssigned_()
        phase = PhaseSpecification({
            "tasks": self.tasks,
            "shared_blocks": self.shared_blocks,
            "communications": self.comms,
            "ranks": self.ranks,
            "id": self.checkID_(0, "phase")
        })

        norm = PhaseSpecificationNormalizer()
        spec = norm.normalize(phase)

        # Write out the spec
        path = os.path.join(os.getcwd(), "spec.yaml") if path is None else path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as output_file:
            yaml.dump(spec, output_file, default_flow_style=False)
