import math
import heapq
import random
import itertools
# from world.map import Map
from utils.coords import Coord
from typing import Dict, Self, Optional, List, Tuple, Dict
from world.tile import Tile
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

JobResult = Optional[Dict[Coord, Coord]]

@dataclass
class Node:
    cost: float
    parent: Optional[Coord] = None
    in_dir: Optional[int] = None
    turns: int = 0



# !!! Need to make this robust to different size entities !!!
# Note: NPC will be size.(x/y) <= 1 for phase so this can be implemented later

class AstarJob:
    """
        Need some good doc strings to explain not using coords and speed ups here (and potentail further speed up)
    """


    def __init__(self, start: Coord, destination: Coord, map, manager):
        self.map = map
        self.start = (int(start.x * 2), int(start.y * 2))
        self.destination = (int(destination.x * 2), int(destination.y * 2))
        self.manager = manager

        # Best-known info per coord
        self.nodes: Dict[Tuple[int, int], Node] = {}
        self.nodes[self.start] = Node(0)

        # Heap entries: (f, turns, rand_tie, counter, coord)
        h0 = self.manhattan_distance_r2(self.start, self.destination)
        self.heap = [(h0, 0, self.start[0], self.start[1])]

        self.path: JobResult = None

    def search(self, cycles: int) -> None:
        while cycles > 0 and self.heap:
            cycles -= 1

            _, heap_cost, n_x, n_y = heapq.heappop(self.heap)
            current = (n_x, n_y)

            # Stale-entry check: if this heap entry doesn't match the best-known g, skip it.
            node = self.nodes.get(current)
            if node is None: node = Node(math.inf, False)

            # Continue if node is stale
            if heap_cost != node.cost: continue

            # If destination is at top of heap return answer
            if current == self.destination:
                self.path = self._reconstruct_path(current)
                return

            # Get and check possible neighbors
            for neighbor, move_dir in self._iter_neighbors(*current):
                neighbor_node = self.nodes[neighbor] if neighbor in self.nodes else Node(math.inf)

                # Pure movement cost (your step cost is 1)
                tentative_g = node.cost + 1

                # Turn counting for tie-break
                prev_dir = node.in_dir
                turned = (prev_dir is not None and prev_dir != move_dir)
                turns = node.turns + (1 if turned else 0)
                tentative_g += turns

                # If this path is better the current path, update the path
                if  tentative_g < neighbor_node.cost:
                    neighbor_node.cost = tentative_g
                    neighbor_node.parent = current
                    neighbor_node.in_dir = move_dir
                    neighbor_node.turns = turns
                    self.nodes[neighbor] = neighbor_node

                    h = self.manhattan_distance_r2(neighbor, self.destination)
                    f = tentative_g + h

                    heapq.heappush(
                        self.heap,
                        (f, tentative_g, neighbor[0], neighbor[1])
                    )

        # Failure case
        if not self.heap:
            self.path = {}

    def _iter_neighbors(self, x: int, y: int):
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
        path: JobResult = {}
        while self.nodes[coord].parent:
            parent = self.nodes[coord].parent
            path[self.manager.get_coord_from_tuple(parent)] = self.manager.get_coord_from_tuple(coord)
            coord = parent

        return path

    def manhattan_distance_r2(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        distance = abs(x1 - x2) + abs(y1 - y2)
        return distance
            
    
                            
class AstarManager:
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
    def add_job(self, start: Coord, destination: Coord) -> int:
        self._require_map()

        id = self._get_id()
        self.jobs[id] = AstarJob(start, destination, self.map, self)
        return id, destination

    def run_jobs(self) -> None:
        total_jobs = len(self.jobs) - len(self.completed_jobs)
        if total_jobs == 0: return
        
        cycles_per_job = self.cpt // total_jobs

        for id, job in self.jobs.items():
            job.search(cycles_per_job)
            if job.path is not None: 
                self.completed_jobs.add(id)

    def get_job_result(self, job: int) -> JobResult:
        if job not in self.completed_jobs: return None
        self.completed_jobs.remove(job)
        result = self.jobs[job].path
        del self.jobs[job]
        self.recycled_ids.append(job)
        return result

    def bind_map(self, map) -> None:
        self.map = map
    
    def reset_map(self) -> None:
        self.map = NotImplemented

    def clear_cache(self):
        self._location_is_valid.cache_clear()

    @staticmethod
    def _default_is_blocked(tile: Tile) -> bool:
        return tile.has_obsticle or tile.is_water
    
    @staticmethod
    def get_coord_from_tuple(location):
        return Coord.math(location[0] / 2, location[1] / 2, 0)
    
    def is_path_unblocked_coords(self, diag: Coord, x_step: Coord, y_step: Coord) -> bool:
        return self._location_is_valid(diag) and self._location_is_valid(x_step) and self._location_is_valid(y_step)

    @lru_cache(maxsize=16384)
    def _location_is_valid(self, location: Coord):
        if tile := self.map.get_tile(self.get_coord_from_tuple(location).floor_world()):
            return not self._default_is_blocked(tile)
        return False
