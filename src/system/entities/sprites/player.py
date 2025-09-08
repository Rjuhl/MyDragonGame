import math
import pygame
from pygame.locals import *
from system.entities.entity import Entity
from typing import List, Dict
from utils.coords import Coord
from constants import TEMP_MOVEMENT_FACTOR, MOVEMENT_MAP

class Player(Entity):
    def __init__(self, location: Coord) -> None:
        is_human = True
        self.init_human(location) if is_human else self.init_dragon(location)

    def update(self, dt, onscreen=True):
        super().update(dt, onscreen)
        self.move(self.get_movement(dt))
        return self


    def init_human(self, location: Coord):
        size = Coord.math(.25, .25, 1.25)
        render_offset = Coord.math(-8, -18, 0)
        img_id = 1
        super().__init__(location, size, img_id, render_offset)

    def init_dragon(self, location: Coord) -> None:
        pass

    # movement in not the same speed in all directions?
    @staticmethod
    def get_movement(dt: float):
        pressed = pygame.key.get_pressed()
        dx = int(pressed[K_d] or pressed[K_RIGHT]) - int(pressed[K_a] or pressed[K_LEFT])
        dy = int(pressed[K_w] or pressed[K_UP]) - int(pressed[K_s] or pressed[K_DOWN])
        
        dx, dy = MOVEMENT_MAP[tuple([dx, dy])]

        dx *= TEMP_MOVEMENT_FACTOR * (dt / 1000) 
        dy *= TEMP_MOVEMENT_FACTOR * (dt / 1000)
         
        return Coord.math(dx, dy, 0)
