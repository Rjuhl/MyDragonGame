import random
from utils.coords import Coord
from system.entities.character import Character
from decorators import register_entity, generate_shadow

@register_entity
@generate_shadow(1, 1, fade=0.5)
class Fox(Character):
    def __init__(self, location: Coord):
        entity_args = [
            location, Coord.math(0, 0, 0), 6, Coord.math(0, 0, 0)
        ]

        super().__init__(
            entity_args,
            20 + random.randint(0, 8), 0, + random.randint(0, 8), 
            30 + random.randint(0, 10), 15, 15, 30 + random.randint(0, 10), 20, 15,
            0.5, 0, 1.25
        )
