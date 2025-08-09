import pygame
from constants import DISPLAY_SIZE
from world.utils.coords import Coord
from system.tile_drawer import TileDrawer

class Renderer:
    def __init__(self, display, map):
        self.map = map
        self.display = display
        self.tile_drawer = TileDrawer(self.display)
        self.view_location = Coord.world(0, 0)
        self.view_location.update_as_view_coord(0, 0)

    def update(self):
        pass
 
    def draw(self):
        tiles_to_render = self.map.get_tiles_to_render(self.view_location)
        for tile in tiles_to_render:
            self.tile_drawer.draw_tile(tile, self.view_location)