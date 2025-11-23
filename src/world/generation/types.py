from enum import Enum

class Biome(Enum):
    DESERT = "Desert"
    GRASSLAND = "Grassland"
    TUNDRA = "tundra"

class Terrain(Enum):
    Air = "Air"
    Water = "Water"
    Ground = "Ground"

class Degree(int, Enum):
    Low = -1
    Medium = 0
    High = 1