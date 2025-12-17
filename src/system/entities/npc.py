from utils.coords import Coord
from system.entities.types.facing_types import Facing
from system.entities.character import Character, CharaterArgs
from typing import List, Any, Optional, Callable, Dict
from world.path_finder import path_finder
from system.entities.spawner import Spawner
from world.generation.types import Terrain

from system.global_vars import game_globals

JobResult = Optional[Dict[Coord, Coord]]

class NPC(Character):
    def __init__(
        self, spawner: Optional[int], entity_args: List[Any], character_args: CharaterArgs
    ):
        super().__init__(entity_args, character_args)

        self.spawner = spawner

        # ------ Pathfinding Attr -------- # 

        self.job_id: Optional[int] = None
        self.path: JobResult = None
        self.next_step = None
        self.destination: Optional[Coord] = None
        self.success_criteria: Callable[[], bool] = self._default_success_criteria

    def set_spawner(self, spawner: int):
        self.spawner = spawner

    def jsonify(self):
        data = super().jsonify()
        data["spawner_id"] = self.spawner
        return data
    
    # ----------------------------------------------------- #
    # -------------        AI helpers        -------------- #
    # ----------------------------------------------------- #


    # TODO: Add detection that the player is not moving to next step
    def set_destination(self, destination: Coord) -> None:
        self.destination = destination
        self.path = None   
        self.next_step = None
        self.job_id = None

    def head_to_destination(self, dt: float) -> Facing:
        if self.destination is None:
            return Facing.Null

        # If no job is running and there is no path to follow, find path
        if self.job_id is None and self.path is None:
            start = self.location.tile_center()
            self.job_id, self.destination = path_finder.add_job(start, self.destination.tile_center())

            movemement = self.location - start
            self.move(movemement)
            
            return self._get_facing(movemement)
        
        # We have a job but it hasnt finished
        elif self.path is None:
            if (path := path_finder.get_job_result(self.job_id)):
                start = self.location.tile_center()
                self.path = path
                self.next_step = self.path[start] if start in self.path else None
                self.job_id = None
                # game_globals.debug_data["fox_path"] = self.path
                # game_globals.debug_data["fox_start"] = start
                # game_globals.debug_data["fox_end"] = self.destination
            else: return Facing.Idle
        
        # If location is not in path we need to find another path
        if self.location.tile_center() not in self.path:
            # TODO: Check if we are close to a path and try to get back on it (Could give nice performance gains)
            print("Location not in path")

            # Search for new path if not close to path
            self.path = None
            self.next_step = None
            start = self.location.tile_center()
            self.job_id, self.destination = path_finder.add_job(start, self.destination.tile_center())
            movemement = self.location - start
            self.move(movemement)
            
            return self._get_facing(movemement)
        
        # Follow path
        current_location = self.location
        last_movement = Coord.math(0, 0, 0)
        max_movement = self.get_speed(Terrain.Ground) * dt / 1000 # Need to make terrain variable in the future
        while max_movement > 0:
            if self.next_step is None: 
                self.destination = None
                return self._get_facing(last_movement)

            # Get get vector for next step
            direction = self.next_step - current_location
            distance = direction.norm()
            
            # If it exceed out movement shorten it
            if distance > max_movement:
                direction *= max_movement / distance
                max_movement = 0
            else: max_movement -= distance
            
            # Update last movement and move the npc
            last_movement = direction
            self.move(last_movement)

            # If we reached the next step update it
            if self.location == self.next_step:
                self.next_step = self.path[self.next_step] if self.next_step in self.path else None
            
        return self._get_facing(last_movement)    


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
        return self.location.manhattan_2D(self.destination) <= 1
    
