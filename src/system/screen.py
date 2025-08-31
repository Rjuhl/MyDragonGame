
import math
import pygame
import numpy as np
from pygame.locals import *
from system.game_clock import game_clock
from utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR
from constants import DISPLAY_SIZE, PADDING, TILE_SIZE, WORLD_HEIGHT
from system.entities.physics.vec3 import Vec3

class Screen:
    def __init__(self):
        self.coord = Coord.world(0, 0)
    
    def location(self): return self.coord.location

    def update(self):
        self.coord.update_as_view_coord(*self.get_movement())
        cam_screen = Coord.BASIS @ self.coord.location 
        cam_screen_i = np.floor(cam_screen + 1e-9)
        self.coord.location = Coord.INV_BASIS @ cam_screen_i

    def get_corners(self):
        return [
            self.coord.as_world_coord(),
            self.coord.copy().update_as_view_coord(DISPLAY_SIZE[0], 0).as_world_coord(),
            self.coord.copy().update_as_view_coord(0, DISPLAY_SIZE[1]).as_world_coord(),
            self.coord.copy().update_as_view_coord(*DISPLAY_SIZE).as_world_coord(),
        ]
    
    def get_bounding_box(self, padding=PADDING):
        corners = self.get_corners()
        min_x = math.floor(min(x for x, _ in corners)) - padding
        max_x = math.ceil(max(x for x, _ in corners)) + padding
        min_y = math.floor(min(y for _, y in corners)) - padding
        max_y = math.ceil(max(y for _, y in corners)) + padding

        return min_x, max_x, min_y, max_y
    
    def git_hitbox(self):
        min_x, max_x, min_y, max_y = self.get_bounding_box()
        size = Vec3(np.array([
            max_x - min_x,
            max_y - min_y,
            WORLD_HEIGHT
        ]) / TILE_SIZE)
        location = Vec3(np.array([min_x, min_y, 0]) / TILE_SIZE)

        return location, size

    
    # movement in not the same speed in all directions?
    @staticmethod
    def get_movement():
        pressed = pygame.key.get_pressed()
        dx = int(pressed[K_d] or pressed[K_RIGHT]) - int(pressed[K_a] or pressed[K_LEFT])
        dy = int(pressed[K_s] or pressed[K_DOWN]) - int(pressed[K_w] or pressed[K_UP])
        
        if dx != 0 and dy != 0:
            dx = math.copysign(1 / math.sqrt(2), dx)
            dy = math.copysign(1 / math.sqrt(2), dy)

        dx *= TEMP_MOVEMENT_FACTOR * (game_clock.dt / 1000)
        dy *= TEMP_MOVEMENT_FACTOR * (game_clock.dt / 1000)
        
        return dx, dy
