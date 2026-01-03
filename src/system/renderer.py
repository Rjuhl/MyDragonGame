import pygame
import numpy as np
from numpy.typing import NDArray

from world.map import Map
from system.screen import Screen
from system.asset_drawer import AssetDrawer

from system.global_vars import game_globals


class Renderer:
    """
        Draws the world to the display surface.

        Responsibilities
        - Render visible tiles (optionally tinted for debug overlays)
        - Render visible entities (sprites + optional hitbox debug)
        - Render optional debug overlays (tracking box, screen hitbox, screen center)

        This class delegates all low-level blitting / tinting / coordinate conversion
        to AssetDrawer. Renderer stays high-level and decides *what* to draw.
    """

    def __init__(self, display: pygame.Surface):
        self.display = display
        self.asset_drawer = AssetDrawer(self.display)

    def draw(self, map: Map, screen: Screen) -> int:
        """ Renders current frame """
        cam_screen_i = screen.cam_offset 
        tiles_to_render = map.get_tiles_to_render(*screen.get_bounding_box())
        for tile in tiles_to_render:
            # Optional overlay: highlight chunk borders in red when toggled on.
            tint = (255, 0, 0) if game_globals.chunk_borders_on and tile.is_chunk_border else None
            
            # Helps show where the "floor" is
            # tint = (0, 0, 255, 128) if tile.location == map.player.location.floor_world() else None

            self.asset_drawer.draw_tile(tile, cam_screen_i, tint)

         # --- Entities ---
        for entity in map.get_entities_to_render():
            self.asset_drawer.draw_sprite(entity, cam_screen_i)

            # Optional overlay: draw hitboxes for non-shadow entities.
            if game_globals.show_hitboxes_on and not entity.isShadow and entity.location and entity.size:
                self.asset_drawer.mark_hitbox(entity.location, entity.size, cam_screen_i, color=(0, 255, 0))

        # --- Debug overlays ---
        # If debug mode is on render debug elements
        if game_globals.render_debug:
            self._render_dubug_elements(map, screen, cam_screen_i)

        # self.asset_drawer.draw_fox_path(cam_screen_i)
        # self.asset_drawer.draw_coords_and_centers(cam_screen_i)

        return len(tiles_to_render)
    
    def _render_dubug_elements(self, map: Map, screen: Screen, cam_screen_i: NDArray[np.float64]) -> None:
        tl, tr, bl, br = screen.get_tracking_box(screen_axis=False)
        self.asset_drawer.blit_dot(tl, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(tr, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(bl, cam_screen_i, (0, 0, 0))
        self.asset_drawer.blit_dot(br, cam_screen_i, (0, 0, 0))

        l, s  = screen.get_hitbox()
        self.asset_drawer.mark_hitbox(l, s, cam_screen_i, color=(0, 255, 0))

        self.asset_drawer.blit_dot(screen.get_screen_center(), cam_screen_i, (0, 0, 0), radius=3)