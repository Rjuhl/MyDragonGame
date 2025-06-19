import pygame
from pathlib import Path

class TileDrawer:
    def __init__(self, display):
        
        paths = []
        current_dir = Path(__file__).parent
        tile_img_dir = current_dir.parent.parent / 'assets' / 'tiles'

        for file in tile_img_dir.iterdir():
            paths.append(file.resolve())
        
        paths.sort()

        self.display = display
        self.imgs = [pygame.image.load(file).convert() for file in paths]
        for img in self.imgs: img.set_colorkey((0, 0, 0))

    def draw_tile(self, id, x, y, display=None):
        working_display = self.display if display is None else display
        working_display.blit(self.imgs[id], x, y)
    
