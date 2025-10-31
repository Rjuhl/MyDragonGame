from utils.coords import Coord
from system.entities.entity import Entity
from decorators import register_entity, generate_shadow

@register_entity
@generate_shadow(1, 1, fade=0.5)
class Fox(Entity):
    def __init__(self, location: Coord):
        super().__init__()