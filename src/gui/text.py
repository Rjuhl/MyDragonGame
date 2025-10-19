import pygame
from pathlib import Path
from gui.component import Component

class PixelText(Component):
    FONT_FILE = Path(__file__).parent  / 'fonts' / 'pixelated.ttf'
    
    def __init__(self, text_content, font_size, font_color):
        self.text = pygame.font.Font(self.FONT_FILE.resolve(), font_size).render(
            text_content, False, font_color
        )
        self.text_rect = self.text.get_rect()
        self.w, self.h = self.text_rect.width, self.text_rect.height

    def render(self, surface):
        surface.blit(self.text, (self.x, self.y))
    
    def get_size(self):
        return self.w, self.h
    



