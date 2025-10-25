import noise
from dataclasses import dataclass, asdict
from world.generation.types import Biome
from system.entities.sprites.tree import Tree
from world.tile import Tile
from utils.coords import Coord
import numpy as np
import random
from typing import Optional, Tuple, List
from system.entities.entity import Entity
from system.entities.base_entity import BaseEntity
from world.biome_tile_weights import TILE_WEIGHTS
from bisect import bisect_left
from decorators import singleton


FOREST_DENSITY = 0.03


@dataclass
class NoiseParams:
    octaves: int 
    persistence: float
    lacunarity: float
    repeatx: int
    repeaty: int
    base: float
       

# Singleton for now, will need to upgrade potentially for multithreading and remove singleton
@singleton
class TerrainGenerator:
    def __init__(self, seed, draw_noise=None):
        self.seed = seed
        self.draw_noise = draw_noise
        self.boime_noise = NoiseParams(
            2, 0.5, 1.5, 10_000, 10_000, seed
        )

        self.forest_noise = NoiseParams(
            2, 1.5, 1.5, 10_000, 10_000, seed
        )

        self.nvs = []
        self.occupied_tiles = {}

        self.rng = random.Random(seed) 


    def _get_biome(self, x: int, y: int):
        noise_value = noise.pnoise2(x / 100, y / 100, **asdict(self.boime_noise))
        if noise_value < -0.2:
            return Biome.DESERT
        elif noise_value < 0.25:
            return Biome.GRASSLAND
        else:
            return Biome.TUNDRA
    
    def _get_id_from_weight(self, weights: Tuple[int, int]) -> int:
        csum, sums, ids = 0, [], []
        for id, weight in weights:
            csum += weight
            sums.append(csum)
            ids.append(id)
        return ids[bisect_left(sums, self.rng.randint(0, csum))]
    
    def _get_tile(self, x: int, y: int, biome: Biome, onborder: bool) -> Tile:
        if biome == Biome.DESERT: return Tile(12, Coord.world(x, y), is_chunk_border=onborder)
        return Tile(
            self._get_id_from_weight(TILE_WEIGHTS[biome]),
            Coord.world(x, y), is_chunk_border=onborder
        )
        
    def _get_tree(self, x: int, y:int, biome: Biome) -> Optional[Tree]:
        if biome == Biome.DESERT: return
        noise_value = noise.pnoise2(x / 100, y / 100, **asdict(self.forest_noise))
        if noise_value < 0 and self.rng.random() < FOREST_DENSITY:
            return Tree(Coord.world(x, y))

    
    def generate_tile(self, x, y, onborder) -> Tuple[Tile, Optional[Entity]]:
        biome = self._get_biome(x, y)
        tile = self._get_tile(x, y, biome, onborder)
        if tree := self._get_tree(x, y, biome):
            return tile, tree
        return tile, None

    
    def get_mm(self):
        print(min(self.nvs), max(self.nvs))
        self.nvs = []
    
    def get_biome_color(self, x, y):
        noise_value = noise.pnoise2(x / 100, y / 100, **asdict(self.draw_noise))
        self.nvs.append(noise_value)
        if noise_value < 0:
            return np.stack((85, 217, 77), axis=-1)
        else:
            return np.stack((0, 0, 0), axis=-1)
    
terrain_generator = TerrainGenerator(0)
