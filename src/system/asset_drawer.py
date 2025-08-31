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

    def draw_tile(self, tile, cam_offset, display=None):
        working_display = self.display if display is None else display
        working_display.blit(self.tiles[tile.id], tile.location.as_view_coord(cam_offset=cam_offset))

    def draw_sprite(self, sprite, cam_offset, display=None):
        working_display = self.display if display is None else display
        working_display.blit(
            self.sprites[sprite.img_id], 
            sprite.location.as_view_coord(cam_offset=cam_offset) + sprite.render_offset.location[:-1]
        )

    def blit_dot(self, world_location, cam_offset, display=None):
        working_display = self.display if display is None else display
        radius = 2
        dot_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, (255, 0, 0), (radius, radius), radius)
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
