from typing import List, Dict
from system.entities.entity import Entity
from utils.coords import Coord


class Tree(Entity):
    def __init__(self, location):
        img_id = 0
        size = Coord.world(1, 1, 2)
        render_offset = Coord.math(-24, -76, 0) # Coord.math(-8, 48, 0)
        super().__init__(location, size, img_id, render_offset)