import pygame
import math
import numpy as np
from constants import DISPLAY_SIZE
from utils.coords import Coord
from system.asset_drawer import AssetDrawer
from system.global_vars import game_globals


class Renderer:
    def __init__(self, display):
        self.display = display
        self.asset_drawer = AssetDrawer(self.display)

    def draw(self, map, screen):
        cam_screen_i = Coord.BASIS @ screen.location()
        tiles_to_render = map.get_tiles_to_render(*screen.get_bounding_box())
        for tile in tiles_to_render:
            tint = (255, 0, 0) if game_globals.chunk_borders_on and tile.is_chunk_border else None
            self.asset_drawer.draw_tile(tile, cam_screen_i, tint)

        for entity in map.get_entities_to_render():
            self.asset_drawer.draw_sprite(entity, cam_screen_i)

        return len(tiles_to_render)