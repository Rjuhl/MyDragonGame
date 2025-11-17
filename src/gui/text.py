import pygame
from pathlib import Path
from gui.component import Component

class PixelText(Component):
    FONTS = {
        0: Path(__file__).parent.parent.parent / 'assets' / 'gui' / 'fonts' / 'PixelGame.otf',
        1: Path(__file__).parent.parent.parent / 'assets' / 'gui' / 'fonts' / 'pixelated.ttf',
    } 
    
    def __init__(self, text_content, font_size, font_color, bold=False, outline=0, outline_color=(0, 0, 0, 255), varient=0):
        self.text_content = text_content
        self.font_size = font_size
        self.font_color = font_color
        self.bold = bold
        self.outline = outline
        self.outline_color = outline_color

        self.font = pygame.font.Font(self.FONTS[varient].resolve(), font_size)
        self.font.set_bold(bold)

        self.text = self.create_text_surface()
        self.text_rect = self.text.get_rect()
        self.w, self.h = self.text_rect.width, self.text_rect.height

    def create_outlined_text(self, base_surface, text_surface, outline_width):
        w, h = base_surface.get_size()

        surf = pygame.Surface((w + outline_width * 2, h + outline_width * 2), pygame.SRCALPHA)

        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                surf.blit(text_surface, (dx + outline_width, dy + outline_width))

        surf.blit(base_surface, (outline_width, outline_width))
        return surf

    def create_text_surface(self):
        base = self.font.render(self.text_content, False, self.font_color)

        if self.outline > 0:
            outline_text = self.font.render(self.text_content, False, self.outline_color)
            return self.create_outlined_text(base, outline_text, self.outline)

        return base

    def render(self, surface):
        surface.blit(self.text, (self.x, self.y))
    
    def get_size(self):
        return self.w, self.h
