from utils.coords import Coord
from collections import deque
from typing import TYPE_CHECKING, Callable, Optional, List

if TYPE_CHECKING:
    from world.map import Map
    from world.tile import Tile

class PathFinder:
    def __init__(self, map: Map):
        self.map = map

    


    def _get_closet_loaded_point(self, point: Coord) -> Optional[Coord]:
        point = point.copy()

        # Get loaded boundry from corner chunks 1 and 9
        x_min, y_max, _ = self.map.chunks[0].tiles[0].location
        x_max, y_min, _ = self.map.chunks[-1].tiles[-1].location

        if self._in_bounds(point, x_max, x_min, y_max, y_min): 
            return self._find_closest_unblocked_point(point, self._default_is_blocked)
        
        if point.x < x_min: point.x = x_min
        if point.x > x_max: point.x = x_max
        if point.y < y_min: point.y = y_min
        if point.y > y_max: point.y = y_max

        return self._find_closest_unblocked_point(point, self._default_is_blocked)



    def _find_closest_unblocked_point(self, point: Coord, is_blocked: Callable[[Tile], bool]) -> Optional[Coord]:

        def get_next_points(coord: Coord, visted: set[Coord]) -> List[Coord]:
            coords = [
                coord.copy().update_as_world_coord(-1, 0),
                coord.copy().update_as_world_coord(1, 0),
                coord.copy().update_as_world_coord(0, -1),
                coord.copy().update_as_world_coord(0, 1)
            ]
            coords = [c for c in coords if c not in visted]
            visted.update(coords)
            return coords

        visted_coords = set(point)
        coord_queue = deque([point])
        while coord_queue:
            if (tile := self.map.get_tile(coord_queue.popleft())):
                if not is_blocked(tile): return tile.location
                coord_queue.extend(get_next_points(tile.location, visted_coords))

    
    @staticmethod
    def _default_is_blocked(tile: Tile) -> bool:
        return tile.has_obsticle or tile.is_water

    @staticmethod
    def _in_bounds(point: Coord, x_max: float, x_min: float, y_max: float, y_min: float) -> bool:
        return x_min <= point.x <= x_max and y_min <= point.y <= y_max

