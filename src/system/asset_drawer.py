import pygame
import numpy as np
from pathlib import Path
from utils.coords import Coord
from utils.types.colors import RGBA
from system.entities.physics.collisions import center_hit_box
from world.tile import Tile
from numpy.typing import NDArray
from system.render_obj import RenderObj
from system.entities.sheet import SheetManager

from system.global_vars import game_globals

class AssetDrawer:
    def __init__(self, display: pygame.Surface):
        current_dir = Path(__file__).parent
        tile_img_dir = current_dir.parent.parent / 'assets' / 'tiles'
        sprite_img_dir = current_dir.parent.parent / 'assets' / 'sprites'
        self.display = display

        self.tiles = self.load_assets(tile_img_dir)
        
        self.sheet_manager = SheetManager(sprite_img_dir)

    def draw_tile(self, tile: Tile, cam_offset: NDArray[np.float64], tint: RGBA, display=None):
        working_display = self.display if display is None else display
        tile_img = self.tiles[tile.id]

        if tint is not None:
            # Copy the original tile
            tinted_img = tile_img.copy()

            # Ensure tile_img has per-pixel alpha
            if tile_img.get_alpha() is None:
                tile_img = tile_img.convert_alpha()

            tinted_img = self._tint_surface(tinted_img, tint)

        else:
            tinted_img = tile_img

        tile_rect = tinted_img.get_rect(center=(tile.location.as_view_coord() - cam_offset))
        working_display.blit(tinted_img, tile_rect)


    def draw_sprite(self, sprite: RenderObj, cam_offset: NDArray[np.float64], display=None) -> None:
        working_display = self.display if display is None else display
        sprite_surface = self.sheet_manager.get_sprite(sprite.id, sprite.frame) if sprite.img is None else sprite.img

        # If mask color is set tint sprite
        if sprite.mask:
            sprite_surface = self._tint_surface(sprite_surface.copy(), sprite.mask)
        
        sprite_rect = sprite_surface.get_rect(center=sprite.draw_location - cam_offset)
        working_display.blit(sprite_surface, sprite_rect)

    def blit_dot(self, world_location: Coord, cam_offset:  NDArray[np.float64], color=(255, 0, 0), radius=2, display=None) -> None:
        working_display = self.display if display is None else display
        dot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, color, (radius, radius), radius)
        x, y = world_location.as_view_coord() - cam_offset
        working_display.blit(dot_surface, (x - radius, y - radius))

    def mark_hitbox(self, loc, size, cam_offset, color=(255, 0, 0), radius=2, display=None, show_upper=True):
        location, _ = center_hit_box(loc, size)
        self.blit_dot(location, cam_offset, color, radius, display)
        self.blit_dot(location + Coord.math(size.x, 0, 0), cam_offset, color, radius, display)
        self.blit_dot(location + Coord.math(0, size.y, 0), cam_offset, color, radius, display)
        self.blit_dot(location + Coord.math(size.x, size.y, 0), cam_offset, color, radius, display)
        self.blit_dot(loc, cam_offset, (255, 0, 0), radius - 1, display)

        if show_upper:
            self.blit_dot(location + Coord.math(0, 0, size.z), cam_offset, (0, 0, 255), radius, display)
            self.blit_dot(location + Coord.math(size.x, 0, size.z), cam_offset, (0, 0, 255), radius, display)
            self.blit_dot(location + Coord.math(0, size.y, size.z), cam_offset, (0, 0, 255), radius, display)
            self.blit_dot(location + size, cam_offset, (0, 0, 255), radius, display)



    def _tint_surface(self, img: pygame.Surface, tint: RGBA):
        mask = pygame.mask.from_surface(img)
        mask_surface = mask.to_surface(setcolor=tint, unsetcolor=(0, 0, 0))
        mask_surface.set_colorkey((0, 0, 0)) 
        img.blit(mask_surface, (0, 0))
        return img


    # def draw_fox_path(self, cam_offset):
    #     if "fox_start" in game_globals.debug_data:
    #         self.blit_dot(game_globals.debug_data["fox_start"], cam_offset, color=(0, 255, 0), radius=4)
    #     if "fox_end" in game_globals.debug_data:
    #         self.blit_dot(game_globals.debug_data["fox_end"], cam_offset, color=(0, 0, 255), radius=4)
    #     if "fox_path" in game_globals.debug_data:
    #         for step in game_globals.debug_data["fox_path"]:
    #             self.blit_dot(step, cam_offset, color=(255, 0, 0), radius=2)

    #     if "fstart" in game_globals.debug_data and isinstance(game_globals.debug_data["fstart"], Coord):
    #         self.blit_dot(game_globals.debug_data["fstart"], cam_offset, color=(0, 0, 0), radius=4)
        
    #     if "fend" in game_globals.debug_data and isinstance(game_globals.debug_data["fend"], Coord):
    #         self.blit_dot(game_globals.debug_data["fend"], cam_offset, color=(0, 0, 0), radius=4)

    
    def draw_coords_and_centers(self, cam_offset):
        coords = [
            Coord.math(0, 0, 0),
            Coord.math(1, 1, 0),
            Coord.math(-1, -1, 0),
            Coord.math(-1, 1, 0),
            Coord.math(1, -1, 0),
        ]

        for coord in coords:
            self.blit_dot(coord, cam_offset, color=(255, 0, 0))
            self.blit_dot(coord.floor_world(), cam_offset, color=(0, 255, 0))
            self.blit_dot(coord.tile_center(), cam_offset, color=(0, 0, 255))
                

    @staticmethod
    def load_assets(path):
        paths = []
        for file in path.iterdir():
            paths.append(file.resolve())
        paths.sort(key=lambda path: int(path.name[:path.name.find('_')]))
        imgs = [pygame.image.load(file).convert_alpha() for file in paths]
        for img in imgs: img.set_colorkey((0, 0, 0))
        return imgs
