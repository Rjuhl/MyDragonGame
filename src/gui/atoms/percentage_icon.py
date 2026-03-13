import pygame
from pathlib import Path
from gui.component import Component
from utils.types.colors import RGBA

class PercentageIcon(Component):
    GUI_FOLDER = Path(__file__).parent.parent.parent.parent / 'assets' / 'gui' / 'icons'
    
    def __init__(self, icon: str, percentage: float = 100, background_color: RGBA = (255, 255, 255, 128)):
        self.percentage = percentage
        self.prev_percentage = percentage
        self.background_color = background_color

        self.source_image = pygame.image.load(self.GUI_FOLDER / icon).convert_alpha()
        self.current_image = self.source_image.copy()
        self.background_image = self._create_background_image()
        self.image_rect = self.source_image.get_rect()
        super().__init__(f"{self.image_rect.width}", f"{self.image_rect.height}")
        
    def set_percentage(self, percentage: float):
        self.percentage = percentage

    def _create_background_image(self):
        bg = pygame.Surface(self.source_image.get_size(), pygame.SRCALPHA)

        src_alpha = pygame.surfarray.pixels_alpha(self.source_image)
        mask = src_alpha > 0
        del src_alpha

        pixels = pygame.surfarray.pixels3d(bg)
        alpha = pygame.surfarray.pixels_alpha(bg)
        pixels[mask] = self.background_color[:3]
        alpha[mask] = self.background_color[3]
        del pixels, alpha

        return bg

    def _update_current_image(self):
        if self.percentage != self.prev_percentage:
            self.prev_percentage = self.percentage

            self.current_image = self.source_image.copy()
            width, height = self.current_image.get_size()
            erase_height = int(height * (1.0 - self.percentage))

            if erase_height > 0:
                erase_rect = pygame.Rect(0, 0, width, erase_height)
                self.current_image.fill((0, 0, 0, 0), erase_rect)

    def render(self, surface):
        self._update_current_image()
        surface.blit(self.background_image, (self.x, self.y))
        surface.blit(self.current_image, (self.x, self.y))
        super().render(surface)