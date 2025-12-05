from enum import Enum

class ShadeLevel(float, Enum):
    GROUND = 0
    GROUND_MASK = 0.1
    BASE_SHADOWS = 0.2
    SPRITE = 1
    CANOPY_START = 2
    CANOPY = 3
    CANOPY_END = 4
    UI = 5