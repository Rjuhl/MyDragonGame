import pygame
import random
from utils.coords import Coord
from system.entities.npc import NPC
from utils.types.shade_levels import ShadeLevel
from decorators import register_entity, generate_shadow

@register_entity
@generate_shadow(0.65, 0.4, fade=0.5)
class Fox(NPC):
    def __init__(self, location: Coord):
        entity_args = [
            location, Coord.math(0.25, 0.25, 0.25), 6, Coord.math(0, -5, 0)
        ]

        super().__init__(
            entity_args,
            20 + random.randint(0, 8), 0, + random.randint(0, 8), 
            30 + random.randint(0, 10), 15, 15, 30 + random.randint(0, 10), 20, 15,
            0.5, 0, 1.25
        )

        self.rotated = False
        self.frame = 0

    def _set_frame(self, frame: int) -> None:
        self.frame = frame
        self.rotated = frame >= 8

    def get_render_objs(self):
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs
    
    def update(self, dt, onscreen):
        super().update(dt, onscreen)
        keys = pygame.key.get_pressed()
        for i in range(10):
            if keys[pygame.K_0 + i]:
                self._set_frame(i - 1)