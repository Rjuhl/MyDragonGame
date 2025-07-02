import pygame
from world.utils.coords import Coord
from system.tile_drawer import TileDrawer

class Renderer:
    def __init__(self, display, map):
        self.map = map
        self.display = display
        self.tile_drawer = TileDrawer(self.display)
        self.view_location = Coord.as_view_coord(0, 0)

    def update(self):
        pass

    def draw(self):
        terrain = self.map.get_map()
        rows, cols = terrain.shape
        for col in range(cols):
            for row in range(rows):
                if terrain[row][col]:
                    x = (col * 16) - (row * 16) - 8
                    y = (row * 8) + (col * 8) - 8
                    self.tile_drawer.draw_tile(0, coord, screen_location)