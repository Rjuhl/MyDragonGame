import pygame
import math
import numpy as np
from constants import DISPLAY_SIZE
from utils.coords import Coord
from system.asset_drawer import AssetDrawer

draw_chunk_border = True

class Renderer:
    def __init__(self, display):
        self.display = display
        self.asset_drawer = AssetDrawer(self.display)

    def draw(self, map, screen):
        cam_screen_i = Coord.BASIS @ screen.location()
        tiles_to_render = map.get_tiles_to_render(*screen.get_bounding_box())
        for tile in tiles_to_render:
            tint = (255, 0, 0) if draw_chunk_border and tile.is_chunk_border else None
            self.asset_drawer.draw_tile(tile, cam_screen_i, tint)

        for entity in map.get_entities_to_render():
            self.asset_drawer.draw_sprite(entity, cam_screen_i)

        self.asset_drawer.blit_dot(screen.get_screen_center(), cam_screen_i, (0, 0, 255), radius=10)

        return len(tiles_to_render)