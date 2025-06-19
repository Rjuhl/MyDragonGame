import pygame
from components.tile_drawer import TileDrawer

class Renderer:
    def __init__(self, display):
        self.display = display
        self.tile_drawer = TileDrawer(self.display)
    

    def update(self):
        pass

    def draw(self):
        pass