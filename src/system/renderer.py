import pygame
import math
import numpy as np
from constants import DISPLAY_SIZE
from world.utils.coords import Coord
from system.tile_drawer import TileDrawer
from system.screen import Screen


class Renderer:
    def __init__(self, display, map):
        self.map = map
        self.display = display
        self.tile_drawer = TileDrawer(self.display)
        self.screen = Screen()

    def update(self):
        self.screen.update()

    def draw(self):
        cam_screen_i = Coord.BASIS @ self.screen.location()
        tiles_to_render = self.map.get_tiles_to_render(self.screen.coord)
        for tile in tiles_to_render:
            self.tile_drawer.draw_tile(tile, cam_screen_i)

        return len(tiles_to_render)