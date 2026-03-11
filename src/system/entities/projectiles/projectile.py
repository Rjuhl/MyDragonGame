from system.entities.entity import Entity
from system.entities.character import Character
from utils.coords import Coord
from typing import List, Optional
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj
from constants import WORLD_HEIGHT, TILE_SIZE

class Projectile(Entity):
    def __init__(
            self, 
            location: Coord, 
            size: Coord, 
            direction: Coord, 
            speed: float, 
            lifespan: int,
            img_id: Optional[int] = None, 
            id: Optional[int] = None
        ):
        render_offset = Coord.math(0, 0, 0)
        super().__init__(location, size, img_id, render_offset, id=id)
    
        self.speed = Coord(speed)
        self.direction = direction / direction.norm()

        self.frame = 0
        self.is_particle = True
        self.send_death_event = False
        self.max_lifespan = lifespan
    
    
    def update(self, dt, onscreen=True):
        super().update(dt, onscreen=onscreen)

        if self.lifespan > self.max_lifespan or not (0 <= self.location.z <= (WORLD_HEIGHT / TILE_SIZE) + 1): 
            self.kill()
            return
        
        self.move(self.direction * self.speed * (dt / 1000))
    
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

    def load_projectile(self, data):
        self.prev_location = Coord.load(data["prev_location"])
        self.lifespan = data["lifespan"]
    
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        super().handle_collision(self_velocity, other_entity, other_velocity, timestep)
        # self.kill()
    
    def deal_damage(self, e: Character) -> float:
        return 0