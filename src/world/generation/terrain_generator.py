import json
import math
import noise
import random
from pathlib import Path
from bisect import bisect_left
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Dict, List

from world.tile import Tile
from utils.coords import Coord
from world.generation.types import Biome
from system.entities.entity import Entity
from world.generation.types import Degree
from system.entities.sprites.tree import Tree
from world.biome_tile_weights import TILE_WEIGHTS


# -----------------------------------------------------------------------------
# Tuning knobs
# -----------------------------------------------------------------------------

# Chance of a tree spawning when forest noise condition passes.
FOREST_DENSITY = 0.03

# How wide the desert<->grassland and grassland<->tundra blend bands are.
BIOME_BLEND_WIDTH = 0.02

# How "soft" the water edge is when comparing noise to the threshold.
# Higher => more gradual shoreline.
WATER_EDGE_SOFTNESS = 0.5

# Base water thresholds per biome (higher => less water in that biome).
WATER_THRESHOLDS: Dict[Biome, float] = {
    Biome.DESERT: 0.84,
    Biome.GRASSLAND: 0.66,
    Biome.TUNDRA: 0.74,
}

# -----------------------------------------------------------------------------
# Noise configuration
# -----------------------------------------------------------------------------

@dataclass
class NoiseParams:
    """ Parameters passed into noise.pnoise2(...) """
    octaves: int 
    persistence: float
    lacunarity: float
    repeatx: int
    repeaty: int
    base: float
       

class TerrainGenerator:
    """
        Procedural terrain + entity (tree) generator.

        Given a seed and high-level sliders (water_level, forest_size, temperature),
        this generator produces:
        - a Tile for each (x, y)
        - optionally an Entity (Tree) for that tile

        High-level pipeline in generate_tile():
        - Compute blended biome weights from "biome noise" + latitude heat map
        - Compute water using lake noise + blended threshold
        - If not water, pick a biome (highest weight) and sample a ground tile id
        - If not water, possibly spawn a tree based on forest noise + density
    """

    def __init__(
        self, 
        seed, 
        water_level: Degree, 
        forest_size: Degree, 
        temperature: Degree, 
        draw_noise=None
    ):
        self.seed = seed
        self.water_level = water_level
        self.forest_size = forest_size
        self.temperature = temperature
        self.draw_noise = draw_noise

        # Noise settings
        self.biome_noise = NoiseParams(3, 0.5, 1.5, 10_000, 10_000, seed)
        self.forest_noise = NoiseParams(2, 1.5, 1.5, 10_000, 10_000, seed)
        self.lake_noise = NoiseParams(2, 0.65, 2.5, 10_000, 10_000, seed)

        # Internal caches
        self.nvs = []
        self.occupied_tiles = {}

        # Convert Degree sliders into scalar modifiers for noise frequency.
        # Smaller modifier => higher frequency noise => "smaller" features.
        self.forest_size_modifier = 100
        if forest_size == Degree.Low:
            self.forest_size_modifier = 50
        elif forest_size == Degree.High:
            self.forest_size_modifier = 200

        self.water_level_modifier = 100
        if water_level == Degree.Low:
            self.water_level_modifier = 50
        elif water_level == Degree.High:
            self.water_level_modifier = 200

        # Deterministic RNG for weighted tile picks / tree chance.
        self.rng = random.Random(seed)

        # Temperature thresholds for biome transitions (tunable).
        # Lower value means "more desert"; higher means "more tundra".
        self._t_desert = -0.35 + self.temperature * 0.1
        self._t_tundra = 0.25 + self.temperature * 0.1


    # -------------------------------------------------------------------------
    # Biome helpers
    # -------------------------------------------------------------------------

    def _get_biome_value(self, x: int, y: int):
        """
        Return a scalar field used to blend biomes.
        - Perlin noise (controls local variation)
        - A cosine "latitude" heat map (controls global north/south climate)
        """
        noise_value = noise.pnoise2(x / 200, y / 200, **asdict(self.boime_noise))
        return noise_value + 0.4 * math.cos(y / 200)
    

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
    
    def _get_biome(self, biome_w) -> Biome:
        """ Collapse biome weights to the single highest-weight biome """
        return max(biome_w.items(), key=lambda kv: kv[1])[0]
        
    # -------------------------------------------------------------------------
    # Water / tile selection
    # -------------------------------------------------------------------------

    def _get_water(self, x: int, y: int, biome_w: Dict[Biome, float], onborder: bool) -> Optional[Tile]:
        """
        Decide whether this position is water.

        Approach:
        - Sample lake noise in [~0..1] (shifted)
        - Compute a blended threshold based on biome weights
        - Use smoothstep around the threshold to soften shore edges
        - If above cutoff, create a water tile with id influenced by biome weights
        """

        lake_noise = noise.pnoise2(
            x / self.water_level_modifier,
            y / self.water_level_modifier,
            **asdict(self.lake_noise),
        ) + 0.5

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

        return Tile(
            self._choose_weighted_id(weights),
            Coord.world(x, y),
            is_chunk_border=onborder,
            is_water=True,
        )
    
    @staticmethod
    def _is_water_tile(tile: Tile) -> bool:
        """Current convention: water tile ids are 13..15 inclusive."""
        return 13 <= tile.id <= 15 
    
    def _get_id_from_weight(self, weights: List[Tuple[int, int]]) -> int:
        """ 
        Given (ids, weights) returns random id influenced by the weights
        Implementation: build cumulative sums and binary search.
        """
        csum, sums, ids = 0, [], []
        for id, weight in weights:
            csum += weight
            sums.append(csum)
            ids.append(id)
        return ids[bisect_left(sums, self.rng.randint(0, csum))]
    
    def _get_tile(self, x: int, y: int, biome_w: Dict[Biome, float], onborder: bool) -> Tile:
        """ Create a Tile at (x, y) based on water and biome """
        if tile := self._get_water(x, y, biome_w, onborder): return tile
        biome = self._get_biome(biome_w)
        if biome == Biome.DESERT: return Tile(12, Coord.world(x, y), is_chunk_border=onborder)
        return Tile(
            self._get_id_from_weight(TILE_WEIGHTS[biome]),
            Coord.world(x, y), is_chunk_border=onborder
        )
    
    # -------------------------------------------------------------------------
    # Entity (tree) spawning
    # -------------------------------------------------------------------------

    def _get_tree(self, x: int, y:int, biome: Biome) -> Optional[Tree]:
        """
        Possibly spawn a Tree entity on land tiles.

        Rules:
        - No trees in desert
        - Forest noise controls clustering
        - FOREST_DENSITY controls density within valid regions
        """

        if biome == Biome.DESERT: return
        
        noise_value = noise.pnoise2(
            x / self.forest_size_modifier,
            y / self.forest_size_modifier,
            **asdict(self.forest_noise),
        )

        if noise_value < 0 and self.rng.random() < FOREST_DENSITY:
            return Tree(Coord.world(x - 0.5, y + 0.5), snowy=(biome==Biome.TUNDRA))
        
    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate_tile(self, x, y, onborder) -> Tuple[Tile, Optional[Entity]]:
        """
        Procedurally generate the tile and (optionally) an entity at world tile (x, y).

        Returns:
            (tile, entity_or_none)
        """

        biome_w = self._biome_weights(x, y)
        biome = self._get_biome(biome_w)
        tile = self._get_tile(x, y, biome_w, onborder)
        if self._is_water_tile(tile): return tile, None
        if tree := self._get_tree(x, y, biome):
            tile.has_obsticle = True
            return tile, tree
        return tile, None

    # -------------------------------------------------------------------------
    # Math helpers / persistence
    # -------------------------------------------------------------------------

    @staticmethod
    def smoothstep(edge0: float, edge1: float, x: float) -> float:
        """
        Hermite smoothstep.
        Returns a smooth 0..1 interpolation of x between edge0 and edge1.
        """
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3 - 2 * t)
    
    def save(self, game_name: str):
        """ Persist generator settings so the same world can be regenerated later """
        path = Path(__file__).parent.parent.parent.parent / 'data' / 'games' / game_name / 'terrain_generator'
        path.write_text(json.dumps(
            {"data": [
                self.seed, self.water_level, self.forest_size, self.temperature
            ]}, ensure_ascii=False, indent=2
        ), encoding='utf-8') 

    @staticmethod
    def load(game_name: str):
        """
        Load generator settings previously written by save().
        Returns None if no saved generator exists.
        """
        path = Path(__file__).parent.parent.parent.parent / 'data' / 'games' / game_name / 'terrain_generator'
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return TerrainGenerator(*data["data"])


# Default generator (used mostly for testing)
default_terrain_generator = TerrainGenerator(0, Degree.Medium, Degree.Medium, Degree.Medium)
