from typing import List, Dict
from system.render_obj import RenderObj
from system.entities.entity import Entity
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from decorators import register_entity, generate_shadow



@register_entity
@generate_shadow(1, 1, shadeLevel=ShadeLevel.CANOPY_START, fade=0.5)
class Tree(Entity):
    def __init__(self, location):
        img_id = None
        self.trunk_img_id = 2
        self.canopy_img_id = 3
        size = Coord.world(0.5, 0.5, 3)
        render_offset = Coord.math(-24, -76, 0) # Coord.math(-8, 48, 0)
        super().__init__(location, size, img_id, render_offset)

    def get_render_objs(self):
        return [
            RenderObj(
                self.trunk_img_id,
                self.draw_location(),
                (ShadeLevel.SPRITE, self.location.x, self.location.y, self.location.z),
                location=self.location, size=self.size
            ),
            RenderObj(
                self.canopy_img_id,
                self.draw_location(),
                (ShadeLevel.CANOPY, self.location.x, self.location.y, self.location.z)
            )
        ]

    @classmethod
    def load(cls, data):
        tree = Tree(Coord.load(data["location"]))

        tree.prev_location = Coord.load(data["prev_location"])
        tree.lifespan = data["lifespan"]

        return tree
