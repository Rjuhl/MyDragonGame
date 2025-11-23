from utils.coords import Coord
from system.entities.types.facing_types import Facing
from system.entities.character import Character, CharaterArgs
from typing import List, Any, Optional, Callable, Dict
from world.path_finder import path_finder
from system.entities.spawner import Spawner


JobResult = Optional[Dict[Coord, Coord]]

class NPC(Character):
    def __init__(
        self, spawner: Optional[Spawner], entity_args: List[Any], character_args: CharaterArgs
    ):
        super().__init__(entity_args, character_args)

        self.spawner = spawner

        # ------ Pathfinding Attr -------- # 

        self.job_id: Optional[int] = None
        self.path: JobResult = None
        self.destination: Optional[Coord] = None
        self.success_criteria: Callable[[], bool] = self._default_success_criteria
    
    # ----------------------------------------------------- #
    # -------------        AI helpers        -------------- #
    # ----------------------------------------------------- #

    def set_destination(self, destination: Coord) -> None:
        self.destination = destination
        self.path = None   
        self.job_id = None

    def head_to_destination(self, dt: float) -> Facing:
        if self.destination is None:
            return Facing.Null

        # If no job is running and there is no path to follow, find path
        if self.job_id is None and self.path is None:
            self.job_id = path_finder.add_job(self.location.floor_world(), self.destination.floor_world())
            return Facing.Idle
        
        # We have a job but it hasnt finished
        elif self.path is None:
            if (path := path_finder.get_job_result(self.job_id)):
                self.path = path
                self.job_id = None
        
        # If location is not in path we need to find another path
        if self.location.floor_world() not in self.path:
            self.path = None
            self.job_id = path_finder.add_job(self.location.floor_world(), self.destination.floor_world())
            return Facing.Idle
        
        # Follow path
        max_movement = self.get_speed() * dt

    def _get_facing(self, movement_vec: Coord):
        dx, dy, _ = movement_vec.location
        if dx == dy == 0: return Facing.Idle
        if dx < 0 and dy > 0: return Facing.Up
        if dx > 0 and dy < 0: return Facing.Down
        if dx < 0 and dy < 0: return Facing.Left
        return Facing.Right

    def set_success_criteria(self, success_criteria_method: Optional[Callable[[], bool]]) -> None:
        self.success_criteria = success_criteria_method if success_criteria_method else self._default_success_criteria

    def at_destination(self) -> bool:
        pass
    
    def _default_success_criteria(self) -> bool:
        if self.destination is None: return True
        return self.location.manhattan_2D(self.destination) <= 2
    
