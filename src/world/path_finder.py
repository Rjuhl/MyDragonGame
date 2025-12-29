from world.tile import Tile
from utils.coords import Coord
from world.astar import AstarManager
from constants import PATH_FINDER_CPT

from collections import deque
from decorators import singleton
from typing import TYPE_CHECKING, Callable, Optional, List

if TYPE_CHECKING:
    from world.tile import Tile

@singleton
class PathFinder(AstarManager):
    """
        High-level pathfinding manager.

        Adds a small convenience layer on top of AstarManager:
        - Ensures the destination is within currently-loaded chunk bounds.
        - If the destination tile is blocked, finds the nearest unblocked tile (BFS).
        - Enforces a singleton pattern so that it can be called easily from anywhere
        - PATH_FINDER_CPT dictates the max nodes per tick explored
    """
     
    def __init__(self, cycles_per_tick: int):
        super().__init__(cycles_per_tick)

    
    def add_job(self, start, destination):
        """ Add a pathfinding job, snapping the destination to the closest loaded and unblocked tile. """
        return super().add_job(start, self._get_closest_loaded_point(destination))


    def _get_closest_loaded_point(self, point: Coord) -> Optional[Coord]:
        self._require_map()

        point = point.copy()

        # Get loaded bounds from corner chunks 1 and 9
        x_min, y_max, _ = self.map.chunks[0].tiles[0].location.location
        x_max, y_min, _ = self.map.chunks[-1].tiles[-1].location.location

        if self._in_bounds(point, x_max, x_min, y_max, y_min): 
            return self._find_closest_unblocked_point(point, self._default_is_blocked)
        
        if point.x < x_min: point.x = x_min
        if point.x > x_max: point.x = x_max
        if point.y < y_min: point.y = y_min
        if point.y > y_max: point.y = y_max

        return self._find_closest_unblocked_point(point.tile_center(), self._default_is_blocked)


    def _find_closest_unblocked_point(self, point: Coord, is_blocked: Callable[[Tile], bool]) -> Optional[Coord]:
        """
            Breadth-first search from `start` (in world coords) to find the closest unblocked tile.

            Uses 4-neighborhood movement (N/S/E/W) in world-tile space.
        """

        def get_next_points(coord: Coord, visited: set[Coord]) -> List[Coord]:
            coords = [
                coord.copy().update_as_world_coord(-1, 0),
                coord.copy().update_as_world_coord(1, 0),
                coord.copy().update_as_world_coord(0, -1),
                coord.copy().update_as_world_coord(0, 1)
            ]
            coords = [c for c in coords if c not in visited]
            visited.update(coords)
            return coords

        visited_coords = {point}
        coord_queue = deque([point])
        while coord_queue:
            if (tile := self.map.get_tile(coord_queue.popleft().floor_world())):
                if not is_blocked(tile): return tile.location
                coord_queue.extend(get_next_points(tile.location, visited_coords))


    @staticmethod
    def _in_bounds(point: Coord, x_max: float, x_min: float, y_max: float, y_min: float) -> bool:
        return x_min <= point.x <= x_max and y_min <= point.y <= y_max

path_finder = PathFinder(PATH_FINDER_CPT)