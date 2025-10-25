from world.generation.types import Biome

BIOME_TILE_WEIGHTS = {  
    "grass": [(0, 32), (1, 2), (2, 2), (3, 2), (4, 1), (5, 1)],
    "snow": [(6, 64), (7, 2), (8, 2), (9, 2), (10, 1), (11, 1)],
    "desert": [(12, 8)]
}

TILE_WEIGHTS = {  
    Biome.GRASSLAND: [(0, 32), (1, 2), (2, 2), (3, 2), (4, 1), (5, 1)],
    Biome.TUNDRA: [(6, 64), (7, 2), (8, 2), (9, 2), (10, 1), (11, 1)],
}