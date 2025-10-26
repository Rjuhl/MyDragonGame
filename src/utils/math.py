import math
import numpy as np
from utils.coords import Coord

def distance_between_coords(c1: Coord, c2: Coord) -> float:
    x, y, z = np.abs((c2 - c1).location)
    return math.sqrt((x ** 2) + (y ** 2) + (z ** 2))