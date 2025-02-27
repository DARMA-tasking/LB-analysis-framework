from typing import Set, List

class JSONSpecFileMaker:

    def __init__(self):
        self.tasks = {}
        self.ranks = {}
        self.phases = {}

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

    def generateNextID_(self, key: str) -> int:
        """ Generic function to generate and update the next available ID for a given category. """
        if key not in self.current_ids or key not in self.id_sets:
            raise ValueError(f"Invalid key: {key}")

        while self.current_ids[key] in self.id_sets[key]:
            self.current_ids[key] += 1

        next_id = self.current_ids[key]
        self.current_ids[key] += 1
        return next_id

    def generateMetadata_(self, rank_id: int) -> dict:
        return {
            "rank": rank_id,
            "type": "LBDatafile"
        }

    def assertIDExists(self, test_id: int, id_type: str):
        assert test_id in self.id_sets[id_type], f"Task {test_id} has not been created yet. Use createTask() method."

    def createTask(self, time: float, seq_id: int = -1, collection_id: int = 7, migratable: bool = True, home = -1, node = -1, user_defined: dict = None) -> dict:
        if seq_id < 0:
            seq_id = self.generateNextID_("seq")

        task = {
            "entity": {
                "collection_id": collection_id,
                "home": home,
                "migratable": migratable,
                "seq_id": seq_id,
                "type": "object"
            },
            "node": node,
            "resource": "cpu",
            "time": time,
        }

        if user_defined is not None:
            task["user_defined"] = user_defined

        self.tasks[seq_id] = tasks

        return task

    def createSharedBlock(self, bytes: float, tasks: List[dict]):
        shared_id = generateNextID("shared")
        shared_block = {}
        for task in tasks:
            self.assertIDExists(task["entity"]["seq_id"], "seq")
            # Create a shared block?
        return shared_block

    def createPhase(self, p_id: int = -1) -> dict:
        if p_id < 0:
            p_id = generateNextID_("phase")
        phase = {
            "id": p_id
        }
        self.phases[p_id] = phase
        return phase

    def createRank(self, r_id: int = -1) -> dict:
        if r_id < 0:
            r_id = generateNextID_("rank")
        rank = {
            "metadata": generateMetadata_(r_id),
            "phases": {} # this is for indexing while building, we need this to be a list by the end
        }
        self.ranks[r_id] = rank
        return rank

    def assignTask(self, task: dict, phase: dict, rank: dict):
        seq_id = task["entity"]["seq_id"]
        self.assertIDExists(seq_id, "seq")
        p_id = phase["id"]
        self.assertIDExists(p_id, "phase")
        r_id = rank["metadata"]["rank"]
        self.assertIDExists(r_id, "rank")

        r = self.ranks[r_id]
        p = self.phases[p_id]

        p["tasks"].append(self.tasks[seq_id])
        r["phases"][p_id] = p

    def write(self):
        for r in self.ranks:
            formatted_r = {
                "metadata": r["metadata"],
                "phases": r["phases"].values()
            }
        # Then write out
