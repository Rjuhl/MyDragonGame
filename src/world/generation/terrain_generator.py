import math
import noise
from dataclasses import dataclass, asdict
from world.generation.types import Biome
from system.entities.sprites.tree import Tree
from world.tile import Tile
from utils.coords import Coord
import numpy as np
import random
from typing import Optional, Tuple, List, Dict
from system.entities.entity import Entity
from system.entities.base_entity import BaseEntity
from world.biome_tile_weights import TILE_WEIGHTS
from bisect import bisect_left
from decorators import singleton


FOREST_DENSITY = 0.03
BIOME_BLEND_WIDTH = 0.02
WATER_EDGE_SOFTNESS = 0.5
WATER_THRESHOLDS: Dict[Biome, float] = {
    Biome.DESERT: 0.84,
    Biome.GRASSLAND: 0.66,
    Biome.TUNDRA: 0.74,
}

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
            3, 0.5, 1.5, 10_000, 10_000, seed
        )
        self.forest_noise = NoiseParams(
            2, 1.5, 1.5, 10_000, 10_000, seed
        )
        self.lake_noise = NoiseParams(
            2, 0.65, 2.5, 10_000, 10_000, seed
        )
        self.nvs = []
        self.occupied_tiles = {}

        self.rng = random.Random(seed) 
        self._t_desert = -0.35
        self._t_tundra =  0.25


    def _get_biome_value(self, x: int, y: int):
        """ Draw value for biome based on perlin noise and cosine heat map """
        noise_value = noise.pnoise2(x / 200, y / 200, **asdict(self.boime_noise))
        return noise_value + 0.4 * math.cos(y / 200)
        
        
    def _get_water(self, x: int, y: int, biome_w: Dict[Biome, float], onborder: bool) -> Optional[Tile]:
        """ Uses lake perlin, biome values, and water weights to smoothly place water """
        
        lake_noise = (noise.pnoise2(x / 100, y / 100, **asdict(self.lake_noise)) + 0.5)
        blended_thresh = (
            biome_w[Biome.DESERT] * WATER_THRESHOLDS[Biome.DESERT] +
            biome_w[Biome.GRASSLAND] * WATER_THRESHOLDS[Biome.GRASSLAND] +
            biome_w[Biome.TUNDRA] * WATER_THRESHOLDS[Biome.TUNDRA]
        )
        m = self.smoothstep(
            blended_thresh - WATER_EDGE_SOFTNESS,
            blended_thresh + WATER_EDGE_SOFTNESS,
            lake_noise
        )

        if m < 0.5: return None

        weights = (
            (13, math.floor(biome_w[Biome.GRASSLAND] * 1000)),
            (14, math.floor(biome_w[Biome.TUNDRA] * 1000)),
            (15, math.floor(biome_w[Biome.DESERT] * 1000)),
        )

        return Tile(self._get_id_from_weight(weights), Coord.world(x, y), is_chunk_border=onborder)
        
    
    def _get_id_from_weight(self, weights: Tuple[int, int]) -> int:
        """ Given (ids, weights) returns random id influenced by the weights"""
        csum, sums, ids = 0, [], []
        for id, weight in weights:
            csum += weight
            sums.append(csum)
            ids.append(id)
        return ids[bisect_left(sums, self.rng.randint(0, csum))]
    
    def _get_tile(self, x: int, y: int, biome_w: Dict[Biome, float], onborder: bool) -> Tile:
        """ Returns the tile for postion x, y """
        if tile := self._get_water(x, y, biome_w, onborder): return tile
        biome = self._get_biome(biome_w)
        if biome == Biome.DESERT: return Tile(12, Coord.world(x, y), is_chunk_border=onborder)
        return Tile(
            self._get_id_from_weight(TILE_WEIGHTS[biome]),
            Coord.world(x, y), is_chunk_border=onborder
        )
        
    def _get_tree(self, x: int, y:int, biome: Biome) -> Optional[Tree]:
        if biome == Biome.DESERT: return
        noise_value = noise.pnoise2(x / 100, y / 100, **asdict(self.forest_noise))
        if noise_value < 0 and self.rng.random() < FOREST_DENSITY:
            return Tree(Coord.world(x, y), snowy=(biome==Biome.TUNDRA))
        

    def _biome_weights(self, x: int, y: int) -> Dict[Biome, float]:
        """ Return smooth weights for (DESERT, GRASSLAND, TUNDRA) that sum to 1. """
        v = self._get_biome_value(x, y)

        d_to_g = self.smoothstep(self._t_desert - BIOME_BLEND_WIDTH, self._t_desert + BIOME_BLEND_WIDTH, v) 
        g_to_t = self.smoothstep(self._t_tundra - BIOME_BLEND_WIDTH, self._t_tundra + BIOME_BLEND_WIDTH, v)  

        w_desert = 1.0 - d_to_g
        w_tundra = g_to_t
        w_grassland = d_to_g * (1.0 - g_to_t)

        s = w_desert + w_grassland + w_tundra
        if s <= 1e-6:
            return { Biome.DESERT:0.0, Biome.GRASSLAND:1.0, Biome.TUNDRA:0.0 }
        
        inv = 1.0 / s
        return {
            Biome.DESERT:    w_desert * inv,
            Biome.GRASSLAND: w_grassland * inv,
            Biome.TUNDRA:    w_tundra * inv,
        }
        
    @staticmethod
    def _is_water_tile(tile: Tile) -> bool:
        return 13 <= tile.id <= 15 

    def _get_biome(self, biome_w) -> Biome:
        """ Collapses to highest weighted biome """
        return max(biome_w.items(), key=lambda kv: kv[1])[0]

    def generate_tile(self, x, y, onborder) -> Tuple[Tile, Optional[Entity]]:
        """ Procedurally generates tile and entities at x, y"""
        biome_w = self._biome_weights(x, y)
        biome = self._get_biome(biome_w)
        tile = self._get_tile(x, y, biome_w, onborder)
        if self._is_water_tile(tile): return tile, None
        if tree := self._get_tree(x, y, biome):
            return tile, tree
        return tile, None


    @staticmethod
    def smoothstep(edge0: float, edge1: float, x: float) -> float:
        """ Hermite smoothstep """
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3 - 2 * t)

    
terrain_generator = TerrainGenerator(0)

