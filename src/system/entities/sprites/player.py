import math
import pygame
from pygame.locals import *
from system.entities.entity import Entity
from typing import List, Dict
from utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR, MOVEMENT_MAP, GRID_RATIO
from system.render_obj import RenderObj
from system.entities.physics.shadows import EllipseData
from utils.types.shade_levels import ShadeLevel
from system.input_handler import input_handler


class Player(Entity):
    def __init__(self, location: Coord) -> None:
        is_human = True
        self.init_human(location) if is_human else self.init_dragon(location)

        self.last_drawn_location = self.location.as_view_coord()
        self.prev_drawn_location = self.location.as_view_coord()

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen)
        self.move(self.get_movement(dt))
        return self

    def init_human(self, location: Coord):
        size = Coord.math(.25, .25, 1.25)
        render_offset = Coord.math(0, -9, 0)
        img_id = 1
        super().__init__(location, size, img_id, render_offset)

    def init_dragon(self, location: Coord) -> None:
        pass

    def smooth_movement(self):
        # Update draw location 
        self.prev_drawn_location = self.last_drawn_location
        dx, dy, dz = self.location.location - self.prev_location.location
        x, y = self.location.as_view_coord()
        if bool(dx) ^ bool(dy) and dz == 0:
            p1_x, p1_y = self.last_drawn_location
            ray_vector = math.copysign(GRID_RATIO[0], dy + dx), math.copysign(GRID_RATIO[1], -dy + dx)
            self.last_drawn_location = self.find_closest_point_on_discrete_ray((x, y), (p1_x, p1_y), ray_vector)
        else:
            self.last_drawn_location = self.location.as_view_coord()

    def shade_level(self):
        if self.location.z <= 1: return ShadeLevel.SPRITE
        elif self.location.z <= 3: return ShadeLevel.CANOPY
        return ShadeLevel.CANOPY_END
    
    def draw_location(self):
        return self.last_drawn_location + self.render_offset.location[:-1]
    
    def get_shadow(self) -> EllipseData:
        x, y = self.last_drawn_location
        return EllipseData(
            Coord.view(x, y, self.location.z),
            0.5, 0.5, 0
        )
    
    # TODO: Better collision handling (ie special handling for static opbjects and so on)
    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        self.move(self_velocity * -timestep)

    
    @staticmethod
    def get_movement(dt: float):
        movement = input_handler.get_player_movement()
        movement *= TEMP_MOVEMENT_FACTOR * (dt / 1000)
        return movement
