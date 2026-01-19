import random
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj
from system.entities.entity import Entity
from system.entities.sprites.player import Player
from system.entities.frame_incrementer import FrameIncrementer
from decorators import register_entity, generate_shadow
from constants import WORLD_HEIGHT, TILE_SIZE
from typing import List, Optional


@register_entity
@generate_shadow(0.15, 0.15, fade=0)
class MagicMissle(Entity):
    TOTAL = 0
    def __init__(self, location: Coord, direction: Coord, id: Optional[int] = None):
        size = Coord.math(0.25, 0.25, 0.25)
        render_offset = Coord.math(0, 0, 0)
        super().__init__(location, size, 11, render_offset, id=id)

        self.speed = Coord.math(8, 8, 8)
        self.direction = direction / direction.norm()

        self.frame = 0
        self.frame_incrementer = FrameIncrementer(0, 83, lambda i: (i + 1) % 4)

        self.send_death_event = False

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen=onscreen)

        if self.lifespan > 1500 or not (0 <= self.location.z <= (WORLD_HEIGHT / TILE_SIZE)): 
            self.kill()
            return
        
        self.move(self.direction * self.speed * (dt / 1000))
        self.frame = self.frame_incrementer.tick()

    
    # Note this could be called more than once per game cycle (could this be causing the bug)
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        
        if isinstance(other_entity, Player):
            other_entity.take_damage(self.deal_damage)

        self.kill()
        
    
    def get_render_objs(self) -> List[RenderObj]:
        render_objs = super().get_render_objs()
        for obj in render_objs: obj.frame = self.frame
        return render_objs
    
    def jsonify(self):
        json = super().jsonify()
        json["direction"] = self.direction.jsonify()
        return json
    
    def shade_level(self):
        if self.location.z <= 1: return ShadeLevel.SPRITE
        elif self.location.z <= 3: return ShadeLevel.CANOPY
        return ShadeLevel.CANOPY_END
    
    def shadow_location(self):
        location = self.location.copy()
        location.z = 0

        return location.as_view_coord() + self.render_offset.location[:-1]

    @staticmethod
    def load(data):
        magic_missle = MagicMissle(
            Coord.load(data["location"]),
            Coord.load(data["direction"]),
            id=data["id"]
        )

        magic_missle.prev_location = Coord.load(data["prev_location"])
        magic_missle.lifespan = data["lifespan"]

        return magic_missle
    
    @staticmethod
    def deal_damage(player: Player) -> float:
        return 8 + random.randint(0, 4)