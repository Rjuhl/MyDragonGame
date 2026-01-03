import pygame
import numpy as np
from pathlib import Path
from utils.coords import Coord
from utils.types.colors import RGB, RGBA
from system.entities.physics.collisions import center_hit_box
from world.tile import Tile
from numpy.typing import NDArray
from system.render_obj import RenderObj
from system.entities.sheet import SheetManager
from typing import List, Optional

from system.global_vars import game_globals

class AssetDrawer:
    """
        Low-level drawing helper for tiles, sprites, and debug overlays.

        Renderer decides *what* to draw. AssetDrawer handles *how* to draw:
        - loading images (tiles + sprite sheets)
        - projecting world coords to view coords (via Coord.as_view_coord())
        - applying camera offsets
        - optional tinting (mask-based color overlay)
        - small debug primitives (dots + hitbox corners)

        Coordinate convention
        - Most draw calls expect world-space inputs and convert to view/screen internally.
        - `cam_offset` is a view-space (vx, vy) offset that gets subtracted from projected
        view coordinates to position objects relative to the camera.
    """

    def __init__(self, display: pygame.Surface):
        self.display = display

        # Dirs
        current_dir = Path(__file__).parent
        tile_img_dir = current_dir.parent.parent / 'assets' / 'tiles'
        sprite_img_dir = current_dir.parent.parent / 'assets' / 'sprites'

        # Tile images are loaded as a list indexed by tile.id
        self.tiles: List[pygame.Surface] = self.load_assets(tile_img_dir)
        
        # Sprite sheets are managed separately (with metadata / frame cropping)
        self.sheet_manager = SheetManager(sprite_img_dir)

    # -------------------------------------------------------------------------
    # Tiles
    # -------------------------------------------------------------------------

    def draw_tile(
        self, 
        tile: Tile, 
        cam_offset: NDArray[np.float64], 
        tint: Optional[RGBA] = None, 
        display: Optional[pygame.Surface] = None
    ) -> None:
        """
        Draw a single tile, optionally tinted.

        Args:
            tile: Tile to draw (tile.id selects image, tile.location selects position).
            cam_offset: View-space camera offset (vx, vy).
            tint: Optional RGBA or RGB color applied as a mask overlay.
            display: Optional target surface; defaults to self.display.
        """

        target = self.display if display is None else display
        base_img = self.tiles[tile.id]

        # Apply tint 
        img = base_img
        if tint is not None:
            img = self._tint_surface(base_img.copy(), tint)

        # Tile is drawn centered at its projected view coordinate.
        center = tile.location.as_view_coord() - cam_offset
        rect = img.get_rect(center=center)
        target.blit(img, rect)

    # -------------------------------------------------------------------------
    # Sprites / entities
    # -------------------------------------------------------------------------

    def draw_sprite(
            self, 
            sprite: RenderObj, 
            cam_offset: NDArray[np.float64],
            display: Optional[pygame.Surface] = None
        ) -> None:
        """
        Draw a RenderObj (entity sprite or shadow object).

        RenderObj provides either:
          - sprite.img: a prebuilt pygame.Surface, OR
          - sprite.id/frame: fetched from the SheetManager

        If sprite.mask is set, the sprite surface is tinted before blitting.
        """

        target = self.display if display is None else display
        sprite_surface = self.sheet_manager.get_sprite(sprite.id, sprite.frame) if sprite.img is None else sprite.img

        # If mask color is set tint sprite
        if sprite.mask:
            sprite_surface = self._tint_surface(sprite_surface.copy(), sprite.mask)
        
        sprite_rect = sprite_surface.get_rect(center=sprite.draw_location - cam_offset)
        target.blit(sprite_surface, sprite_rect)

    # -------------------------------------------------------------------------
    # Debug primitives
    # -------------------------------------------------------------------------

    def blit_dot(
        self, 
        world_location: Coord, 
        cam_offset:  NDArray[np.float64],
        color: RGB = (255, 0, 0),
        radius: int = 2,
        display: Optional[pygame.Surface] = None
    ) -> None:
        """ Draw a small dot at a world location (projected to view coords) """
        target = self.display if display is None else display

        dot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, color, (radius, radius), radius)

        x, y = world_location.as_view_coord() - cam_offset
        target.blit(dot_surface, (x - radius, y - radius))

    def mark_hitbox(
        self, 
        loc: Coord, 
        size: Coord, 
        cam_offset: NDArray[np.float64],
        color: RGB = (255, 0, 0),
        radius: int = 2, 
        display: Optional[pygame.Surface] = None,
        show_upper: bool = True
    ) -> None:
        """
        Visualize an entity hitbox by drawing dots on the 3D AABB corners.

        - Uses center_hit_box() to convert from center-based entity location to top-left.
        - Draws the 4 bottom corners in `color`.
        - Optionally draws the 4 top corners in blue (z + size.z) if show_upper.
        - Also draws the entity center (loc) in red for reference.
        """

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
        """ Apply a tint using a mask derived from the sprite's non-transparent pixels """
        mask = pygame.mask.from_surface(img)
        mask_surface = mask.to_surface(setcolor=tint, unsetcolor=(0, 0, 0))
        mask_surface.set_colorkey((0, 0, 0)) 
        img.blit(mask_surface, (0, 0))
        return img
    
    # -------------------------------------------------------------------------
    # Asset Loading
    # -------------------------------------------------------------------------

    @staticmethod
    def load_assets(path):
        """
        Load a directory of images into a list sorted by numeric prefix.

        Expected file naming convention:
            <id>_<name>.<ext>

        Returns:
            list[Surface] where index == <id>
        """

        files = [p.resolve() for p in path.iterdir() if p.is_file()]

        # Sort by numeric prefix before the first underscore.
        files.sort(key=lambda p: int(p.name.split("_", 1)[0]))
        imgs = [pygame.image.load(f).convert_alpha() for f in files]
        for img in imgs: img.set_colorkey((0, 0, 0)) # TODO: Remove this and make tiles assets transparent

        return imgs


    # -------------------------------------------------------------------------
    # MISC
    # -------------------------------------------------------------------------

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
                