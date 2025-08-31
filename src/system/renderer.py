import pygame
import math
import numpy as np
from constants import DISPLAY_SIZE
from utils.coords import Coord
from system.asset_drawer import AssetDrawer



class Renderer:
    def __init__(self, display):
        self.display = display
        self.tile_drawer = AssetDrawer(self.display)

    def draw(self, map, screen):
        cam_screen_i = Coord.BASIS @ screen.location()
        tiles_to_render = map.get_tiles_to_render(*screen.get_bounding_box())
        for tile in tiles_to_render:
            self.tile_drawer.draw_tile(tile, cam_screen_i)

        return len(tiles_to_render)