import pygame
from pathlib import Path

class AssetDrawer:
    def __init__(self, display):
        current_dir = Path(__file__).parent
        tile_img_dir = current_dir.parent.parent / 'assets' / 'tiles'
        sprite_img_dir = current_dir.parent.parent / 'assets' / 'sprites'
        self.display = display

        self.tiles = self.load_assets(tile_img_dir)
        self.sprites = self.load_assets(sprite_img_dir)

    def draw_tile(self, tile, cam_offset, tint, display=None):
        working_display = self.display if display is None else display
        tile_img = self.tiles[tile.id]

        if tint is not None:
            # Copy the original tile
            tinted_img = tile_img.copy()

            # Ensure tile_img has per-pixel alpha
            if tile_img.get_alpha() is None:
                tile_img = tile_img.convert_alpha()

            # Create a mask of non-black (visible) pixels
            mask = pygame.mask.from_surface(tile_img)

            # Create a surface with the tint color (fully opaque red)
            mask_surface = mask.to_surface(setcolor=tint, unsetcolor=(0, 0, 0))
            mask_surface.set_colorkey((0, 0, 0))  # ignore black (unset pixels)

            # Blit the red-tinted mask on top of the tile
            tinted_img.blit(mask_surface, (0, 0))

        else:
            tinted_img = tile_img

        working_display.blit(tinted_img, tile.location.as_view_coord(cam_offset=cam_offset))


    def draw_sprite(self, sprite, cam_offset, display=None):
        working_display = self.display if display is None else display
        working_display.blit(
            self.sprites[sprite.img_id], 
            sprite.location.as_view_coord(cam_offset=cam_offset) + sprite.render_offset.location[:-1]
        )

    def blit_dot(self, world_location, cam_offset, color=(255, 0, 0), radius=2, display=None):
        working_display = self.display if display is None else display
        dot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, color, (radius, radius), radius)
        x, y = world_location.as_view_coord(cam_offset=cam_offset)
        working_display.blit(dot_surface, (x - radius, y - radius))

    @staticmethod
    def load_assets(path):
        paths = []
        for file in path.iterdir():
            paths.append(file.resolve())
        paths.sort(key=lambda path: int(path.name[:path.name.find('_')]))
        imgs = [pygame.image.load(file).convert() for file in paths]
        for img in imgs: img.set_colorkey((0, 0, 0))
        return imgs
