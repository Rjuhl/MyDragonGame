"""
A* pathfinding job/manager.

Design notes
- Coordinates are stored internally as "r2" (x2): tile-centers are doubled (x*2, y*2)
  so half-tile moves can be represented with integers.
- The job returns a dict mapping parent Coord -> child Coord for reconstructing a path.
- Turn cost is used as a *tie-break-ish* factor by adding turns into the g-cost.

Assumptions
- start/destination are tile centers in world coordinates.
- Entity size is 1 tile for now (commented TODO).
"""

import math
import heapq
from dataclasses import dataclass
from functools import lru_cache

from world.tile import Tile
from utils.coords import Coord
from typing import Dict, Optional, Tuple, Dict

from metrics.simple_metrics import timeit


# Job result maps "from" -> "to" for each step (parent -> child).
JobResult = Optional[Dict[Coord, Coord]]

# Internal coordinate type (r2 integer grid).
GridCoord = Tuple[int, int]


@dataclass
class Node:
    """
    Stores best-known path info for a node in the A* search graph.

    cost: Best-known g-cost to reach this node.
    parent: Parent grid coord used to reconstruct the path.
    in_dir: Direction used to enter this node (used for turn counting).
    turns: Total turns taken to reach this node (tie-break / additional cost).
    """
    cost: float
    parent: Optional[GridCoord] = None
    in_dir: Optional[int] = None
    turns: int = 0



# TODO: Make robust to different-size entities.
# Note: NPC is size.(x/y) <= 1 for now, so this can be implemented later.
class AstarJob:
    """
        Encapsulates a single pathfinding request executed via A*.

        For performance, this job uses integer tuples (x2 coords) internally rather than Coord.
        It assumes the start/destination are centered in their tiles.
    """


    def __init__(self, start: Coord, destination: Coord, map, manager):
        self.map = map
        self.start = (int(start.x * 2), int(start.y * 2))
        self.destination = (int(destination.x * 2), int(destination.y * 2))
        self.manager = manager

        # Best-known info per coord
        self.nodes: Dict[Tuple[int, int], Node] = {}
        self.nodes[self.start] = Node(0)

        # Heap entries:
        #   (f, turns, g, x, y)
        #
        # Where:
        #   g = distance-only path length so far
        #   turns = used ONLY as a tie-breaker (fewest turns among equal-distance paths)
        h0 = self.chebyshev_distance_r2(self.start, self.destination)
        self.heap = [(h0, 0, 0, self.start[0], self.start[1])]

        self.path: JobResult = None

    def search(self, cycles: int) -> None:
        """
            Find a path with:
            1) minimum steps
            2) among those, minimum turns (direction changes)

            Processes at most `cycles` pops per call.
            Sets self.path to a dict (success), {} (failure), or keeps None (in progress).
        """

        EPS = 1e-6  # tiny bias; doesn't change distance meaningfully, just ordering

        while cycles > 0 and self.heap:
            cycles -= 1

            f, heap_turns, heap_g, n_x, n_y = heapq.heappop(self.heap)
            current = (n_x, n_y)

            node = self.nodes.get(current)
            if node is None:
                continue

            # Stale-entry check
            if heap_g != node.cost or heap_turns != node.turns:
                continue

            if current == self.destination:
                self.path = self._reconstruct_path(current)
                return

            for neighbor, move_dir in self._iter_neighbors(*current):
                neighbor_node = self.nodes[neighbor] if neighbor in self.nodes else Node(math.inf)

                # Distance-only g
                tentative_g = node.cost + 1

                # Turn counting
                prev_dir = node.in_dir
                turned = (prev_dir is not None and prev_dir != move_dir)
                turns = node.turns + (1 if turned else 0)

                better = (
                    tentative_g < neighbor_node.cost
                    or (tentative_g == neighbor_node.cost and turns < neighbor_node.turns)
                )

                if better:
                    neighbor_node.cost = tentative_g
                    neighbor_node.parent = current
                    neighbor_node.in_dir = move_dir
                    neighbor_node.turns = turns
                    self.nodes[neighbor] = neighbor_node

                    h = self.chebyshev_distance_r2(neighbor, self.destination)

                    # Priority: A* first, then strongly prefer fewer turns via epsilon.
                    f = tentative_g + h + EPS * turns

                    heapq.heappush(self.heap, (f, turns, tentative_g, neighbor[0], neighbor[1]))

        # Failure case
        if not self.heap:
            self.path = {}

    def _iter_neighbors(self, x: int, y: int):
        """
            Yield (neighbor_coord, direction) for all valid diagonal-ish moves
            permitted by  blocking rules.

            Direction encoding preserved from original:
                0: (-1, -1)
                1: (+1, +1)
                2: (+1, -1)
                3: (-1, +1)
        """

        # step in x2 coords (half-tile in world space)
        c = 1  

        # pre-bind for speed
        is_ok = self.manager.is_path_unblocked_coords
        yield_from = (
            (x - c, y - c, 0),
            (x + c, y + c, 1),
            (x + c, y - c, 2),
            (x - c, y + c, 3),
        )
        for nx, ny, d in yield_from:
            if is_ok((nx, ny), (nx, y), (x, ny)):
                yield (nx, ny), d

    def _reconstruct_path(self, coord: tuple[int, int]) -> JobResult:
        """ Reconstruct parent->child mapping in world Coord space (converting from x2 coords). """
        path: JobResult = {}
        while self.nodes[coord].parent:
            parent = self.nodes[coord].parent
            path[self.manager.get_coord_from_tuple(parent)] = self.manager.get_coord_from_tuple(coord)
            coord = parent

        return path

    def chebyshev_distance_r2(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        return max(dx, dy)         
               
class AstarManager:
    """
        Manages multiple concurrent A* jobs and shares cached tile-validity checks.
    """
    def __init__(self, cycles_per_tick: int):
        self.map = None
        self.cpt = cycles_per_tick
    
        self.job_id = -1
        self.recycled_ids = []
        
        self.jobs: Dict[int, AstarJob] = {}
        self.completed_jobs: set[int] = set()

    def _get_id(self):
        if len(self.recycled_ids) > 0: return self.recycled_ids.pop()
        
        self.job_id += 1
        return self.job_id
    
    def _require_map(self) -> None:
        if self.map is None:
            raise ValueError("Map is required but not set.")

    # Start is expected to be the center of a tile
    def add_job(self, start: Coord, destination: Coord) -> Tuple[int, Coord]:
        """ Creates Astar job. Returns id and updated destination """
        self._require_map()

        id = self._get_id()
        self.jobs[id] = AstarJob(start, destination, self.map, self)
        return id, destination
 
    @timeit()
    def run_jobs(self) -> None:
        """ Advance all jobs by splitting cycles-per-tick across the number of active jobs. """

        total_jobs = len(self.jobs) - len(self.completed_jobs)
        print(f"There are {total_jobs} jobs running right now ({len(self.jobs)}/{len(self.completed_jobs)})")
        if total_jobs == 0: return
        
        cycles_per_job = self.cpt // total_jobs

        for id, job in self.jobs.items():
            if job.path is not None: continue
            job.search(cycles_per_job)
            if job.path is not None: 
                self.completed_jobs.add(id)

    # Note: Jobs completed but never retrieved can gunk up the works
    # Jobs with path are not cycled again -- should help relieve load
    def get_job_result(self, job: int) -> JobResult:
        """ Fetch and remove a completed job result. Returns None if not complete yet. """
        if job not in self.completed_jobs: return None
        self.completed_jobs.remove(job)
        result = self.jobs[job].path
        del self.jobs[job]
        self.recycled_ids.append(job)
        return result

    def bind_map(self, map) -> None:
        """Attach a map reference used for tile blocking checks."""
        self.map = map
    
    def reset_map(self) -> None:
        """Detach the map and clear caches."""
        self.map = None
        self.clear_cache()

    def clear_cache(self):
        """Clear cached validity results (call if map changes or chunks loads/unloads)."""
        self._location_is_valid.cache_clear()


    # --- Tile / blocking rules -------------------------------------------------

    @staticmethod
    def _default_is_blocked(tile: Tile) -> bool:
        return tile.has_obsticle or tile.is_water
    
    @staticmethod
    def get_coord_from_tuple(location):
        """Convert x2 integer coords back into Coord space."""
        return Coord.math(location[0] / 2, location[1] / 2, 0)
    
    def is_path_unblocked_coords(self, diag: Coord, x_step: Coord, y_step: Coord) -> bool:
        """
        A diagonal move is allowed only if:
        - diagonal target is valid, and
        - the horizontal step is valid, and
        - the vertical step is valid.
        """
        return (
            self._location_is_valid(diag)
            and self._location_is_valid(x_step)
            and self._location_is_valid(y_step)
        )

    @lru_cache(maxsize=16384)
    def _location_is_valid(self, location: Coord):
        """
            Cached: returns True if the tile at `location` is not blocked.
            Location is in x2 integer coords.
        """
        if tile := self.map.get_tile(self.get_coord_from_tuple(location).floor_world()):
            return not self._default_is_blocked(tile)
        return False
