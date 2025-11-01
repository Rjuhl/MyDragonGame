import random
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj
from system.entities.entity import Entity
from gui.text import PixelText
from typing import Callable, List


class DamageText(Entity):
    def __init__(self, location: Coord, num: int, kill_age: float, trajectory: Callable[[float], Coord], with_rng=False):
        super().__init__(location, Coord.math(1e-1, 1e-1, 1e-1), -1, Coord.math(0, 0, 0), id=-1, solid=False)
        self.kill_age = kill_age
        self.trajectory = trajectory
        self.with_rng = with_rng
        self.img = PixelText(str(num), 8, (238, 18, 66, 255)).text

        self.base_render_offset = self.render_offset
        self.multiplier = 1
        self.solid = False

        if self.with_rng:
            if random.random() < 0.5: self.multiplier = -1
            self.base_render_offset  = Coord.view(random.randint(0, 4), random.randint(0, 4), 0)

    def update(self, dt, onscreen=True):
        super().update(dt)
        if self.lifespan > self.kill_age:
            self.kill()

        self.render_offset = self.base_render_offset + Coord.math(self.multiplier * self.lifespan / 100, -self.trajectory(self.lifespan), 0)
   
    def shade_level(self):
        return ShadeLevel.UI

    def get_render_objs(self) -> List[RenderObj]:
        return [RenderObj(
            self.img_id,
            self.draw_location(),
            (self.shade_level(), self.location.x, self.location.y, self.location.z),
            location=self.location, size=self.size, img=self.img
        )]
    
    # Don't save damage text
    def jsonify():
        return None