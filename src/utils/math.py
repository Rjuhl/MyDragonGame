import math
import numpy as np
from utils.coords import Coords

def distance_between_coords(self, c1, c2):
    x, y, z = np.abs((c2 - c1).location)
    return math.sqrt((x ** 2) + (y ** 2) + (z ** 2))