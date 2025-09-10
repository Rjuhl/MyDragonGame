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
        cam_screen_i = screen.cam_offset 
        # print(cam_screen_i)
        tiles_to_render = map.get_tiles_to_render(*screen.get_bounding_box())
        for tile in tiles_to_render:
            # Set tile color to red if on chunk border and chunk borders on has been toggled on
            tint = (255, 0, 0) if game_globals.chunk_borders_on and tile.is_chunk_border else None
            self.asset_drawer.draw_tile(tile, cam_screen_i, tint)

        for entity in map.get_entities_to_render():
            self.asset_drawer.draw_sprite(entity, cam_screen_i)

            # If hitboxes are turned on draw hitbox corners
            if game_globals.show_hitboxes_on:
                self.asset_drawer.mark_hitbox(entity.location, entity.size, cam_screen_i, color=(0, 255, 0))

        
        # If debug mode is on render debug elements
        if game_globals.render_debug:
            self._render_dubug_elements(map, screen, cam_screen_i)

        return len(tiles_to_render)
    
    def _render_dubug_elements(self, map, screen, cam_screen_i):
        tl, tr, bl, br = screen.get_tracking_box(screen_axis=False)
        self.asset_drawer.blit_dot(tl, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(tr, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(bl, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(br, cam_screen_i, (0, 0, 0))

        l, s  = screen.get_hitbox()
        self.asset_drawer.mark_hitbox(l, s, cam_screen_i, color=(0, 255, 0))

        self.asset_drawer.blit_dot(screen.get_screen_center(), cam_screen_i, (0, 0, 0), radius=3)