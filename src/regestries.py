import math
import random
from constants import BLANK_WEIGHT
from typing import Optional
from bisect import bisect_left

ENTITY_REGISTRY: dict[str, type] = {}
SHADOW_ENTITY_REGISTRY: dict[type, tuple[float]] = {}
PAGE_REGISTRY: dict[type, bool] = {}
CHUNK_SPAWNER_REGISTRY: list[type] = []

class ChunkSpawnerRegistry:
    def __init__(self):
        self.types = CHUNK_SPAWNER_REGISTRY
        self.weights = [BLANK_WEIGHT]

        for t in self.types:
            self.weights.append(self.weights[-1] + t.SPAWN_WEIGHT)
    
    def choose_random_type(self) -> Optional[type]:
        rand_num = random.randint(0, math.floor(self.weights[-1]))
        index = bisect_left(self.weights, rand_num)
        if index == 0: return None
        return self.types[index - 1]
