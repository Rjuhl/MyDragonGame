import math
import heapq
import random
from world.map import Map
from utils.coords import Coord
from typing import Dict, Self, Optional, List, Callable, Dict
from world.tile import Tile
from collections import defaultdict
from dataclasses import dataclass

JobResult = Optional[Dict[Coord, Coord]]

@dataclass
class Node:
    cost: float
    explored: bool
    parent: Optional[Coord] = None


class AstarJob:
    def __init__(self, start: Coord, destination: Coord, map: Map, is_blocked: Callable[[Tile], bool]):
        self.map = map
        self.start = start
        self.destination = destination
        self.is_blocked = is_blocked

        self.heap = [(self.start.manhattan_2D(self.destination), start)]
        self.nodes: Dict[Coord, Node] = defaultdict(lambda: Node(math.inf, False))
        self.nodes[start] = Node(0, False)

        self.path: JobResult = None

    def search(self, cycles: int) -> None:
        while cycles > 0 and self.heap:
            cycles -= 1
            _, current_node = heapq.heappop(self.heap)

            if self.nodes[c_neighboor].explored: continue

            if current_node == self.destination: 
                self.path = self._reconstruct_path(current_node)
                return
                
            
            for c_neighboor in self._get_neighbors(current_node):
                if self.nodes[current_node].cost + 1 < self.nodes[c_neighboor].cost:
                    self.nodes[c_neighboor].cost = self.nodes[current_node].cost + 1
                    self.nodes[c_neighboor].parent = current_node

                    heapq.heappush(
                        self.heap, 
                        (self.nodes[c_neighboor].cost + c_neighboor.manhattan_2D(self.destination), c_neighboor)
                    )
            
            self.nodes[current_node].explored = True        

        # Failure case
        if not self.heap: self.path = {}

    def _get_neighbors(self, coord: Coord) -> List[Coord]:
        coords = [
            coord.copy().update_as_world_coord(-1, 0),
            coord.copy().update_as_world_coord(1, 0),
            coord.copy().update_as_world_coord(0, -1),
            coord.copy().update_as_world_coord(0, 1)
        ]

        neighbors = []
        for c in coords:
            if (tile := self.map.get_tile(c)):
                if not tile.has_obsticle and not tile.is_water:
                    neighbors.append(tile.location.copy())

        random.shuffle(neighbors)

        return neighbors
    

    def _reconstruct_path(self, coord: Coord) -> JobResult:
        path = {}
        while self.nodes[coord].parent:
            path[self.nodes[coord].parent] = coord
            coord = self.nodes[coord].parent
        return path
            
    
                              
class AstarManager:
    def __init__(self, cycles_per_tick: int):
        self.map = None
        self.cpt = cycles_per_tick
    
        self.job_id = -1
        self.recycled_ids = []
        
        self.jobs: Dict[int, AstarJob] = {}
        self.completed_jobs: set[int] = set()

    def _get_id(self):
        if len(self.recycled_ids > 0): return self.recycled_ids.pop()
        
        self.job_id += 1
        return self.job_id
    
    def _require_map(self) -> None:
        if self.map is None:
            raise ValueError("Map is required but not set.")

    def add_job(self, start: Coord, destination: Coord) -> int:
        self._require_map()

        id = self._get_id()
        self.jobs[id] = AstarJob(start, destination, self.map, self._default_is_blocked)
        return id

    def run_jobs(self) -> None:
        total_jobs = len(self.jobs) - len(self.completed_jobs)
        cycles_per_job = self.cpt // total_jobs

        for id, job in self.jobs.items():
            job.search(cycles_per_job)
            if job.path: self.completed_jobs.add(id)

    def get_job_result(self, job: int) -> JobResult:
        if job not in self.completed_jobs: return None
        
        self.completed_jobs.remove(job)
        result = self.jobs[job]
        del self.jobs[job]
        
        self.recycled_ids.append(job)
        return result

    def bind_map(self, map: Map) -> None:
        self.map = map
    
    def reset_map(self) -> None:
        self.map = NotImplemented

    @staticmethod
    def _default_is_blocked(tile: Tile) -> bool:
        return tile.has_obsticle or tile.is_water
