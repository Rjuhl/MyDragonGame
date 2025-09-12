from typing import List, Dict
from system.entities.entity import Entity
from utils.coords import Coord
from decorators import register_entity

@register_entity
class Tree(Entity):
    def __init__(self, location):
        img_id = 0
        size = Coord.world(0.5, 0.5, 2)
        render_offset = Coord.math(-24, -76, 0) # Coord.math(-8, 48, 0)
        super().__init__(location, size, img_id, render_offset)

    def load(self, data):
        tree = Tree(Coord.load(data["location"]))

        tree.prev_location = Coord.load(data["prev_location"])
        tree.lifespan = data["lifespan"]

        return tree
