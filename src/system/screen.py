
import math
import pygame
import numpy as np
from pygame.locals import *
from system.game_clock import game_clock
from world.utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR

class Screen:
    def __init__(self):
        self.coord = Coord.world(0, 0)
    
    def location(self): return self.coord.location

    def update(self):
        self.coord.update_as_view_coord(*self.get_movement())
        cam_screen = Coord.BASIS @ self.coord.location 
        cam_screen_i = np.floor(cam_screen + 1e-9)
        self.coord.location = Coord.INV_BASIS @ cam_screen_i
    
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
