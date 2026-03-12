import random
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj
from system.entities.entity import Entity
from system.entities.sprites.player import Player
from system.entities.frame_incrementer import FrameIncrementer
from decorators import register_entity, generate_shadow
from constants import WORLD_HEIGHT, TILE_SIZE
from system.entities.projectiles.projectile import Projectile
from typing import List, Optional


# @register_entity
@generate_shadow(0.15, 0.15, fade=0)
class MagicMissle(Projectile):
    TOTAL = 0
    def __init__(self, location: Coord, direction: Coord, id: Optional[int] = None):
        size = Coord.math(0.25, 0.25, 0.25)
        super().__init__(location, size, direction, 8, 1500, img_id=11, id=id)

        self.frame_incrementer = FrameIncrementer(0, 83, lambda i: (i + 1) % 4)


    def update(self, dt, onscreen=True):
        super().update(dt, onscreen=onscreen)
        self.frame = self.frame_incrementer.tick()

    
    # Note this could be called more than once per game cycle (could this be causing the bug)
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):

        # Can also just spawn the mm slightly higher
        from system.entities.sprites.wizard import Wizard
        if isinstance(other_entity, Wizard): 
            return

        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        
        if isinstance(other_entity, Player):
            other_entity.take_damage(self.deal_damage)

        self.kill()
        
    
    # def jsonify(self):
    #     json = super().jsonify()
    #     json["direction"] = self.direction.jsonify()
    #     return json

    # @staticmethod
    # def load(data):
    #     magic_missle = MagicMissle(
    #         Coord.load(data["location"]),
    #         Coord.load(data["direction"]),
    #         id=data["id"]
    #     )

    #     magic_missle.prev_location = Coord.load(data["prev_location"])
    #     magic_missle.lifespan = data["lifespan"]

    #     return magic_missle
    
    @staticmethod
    def deal_damage(player: Player) -> float:
        return 8 + random.randint(0, 4)