import pygame
from pathlib import Path
from gui.component import Component

class PercentageIcons(Component):
    GUI_FOLDER = Path(__file__).parent.parent.parent / 'assets' / 'gui'
    
    def __init__(self, icon: str, percentage: float = 100):
        self.percentage = percentage
        self.prev_percentage = percentage

        self.source_image = pygame.image.load(self.GUI_FOLDER / icon).convert_alpha()
        self.current_image = self.source_image.copy()
        self.image_rect = self.source_image.get_rect()
        super().__init__(f"{self.image_rect.width}", f"{self.image_rect.height}")
        
    def set_percentage(self, percentage: float):
        self.percentage = percentage

    def _update_current_image(self):
        if self.percentage != self.prev_percentage:
            self.prev_percentage = self.percentage

            self.current_image = self.source_image.copy()
            width, height = self.current_image.get_size()
            erase_height = int(height * (1.0 - self.percentage / 100.0))

            if erase_height > 0:
                erase_rect = pygame.Rect(0, 0, width, erase_height)
                self.current_image.fill((0, 0, 0, 0), erase_rect)

    def render(self, surface):
        self._update_current_image()
        surface.blit(self.current_image, (self.x, self.y))
        super().render(surface)