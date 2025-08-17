import math
import random
from pygame.locals import *
from world.utils.coords import Coord
from world.chunk import Chunk
from world.biome_tile_weights import BIOME_TILE_WEIGHTS
from constants import DISPLAY_SIZE, PADDING

# Updates chunk list based on player location
# Chunk ordering:
#     1   4   7
#     2   5   8
#     3   6   9


class Map:

    def __init__(self, location):
        self.chunks = []
        self.location = location
        self.init_map_chunks()
    
    # TODO: Needs to update location. If locations crosses to new chunk, load new chunks
    def update_location(self, dx, dy):
        pass

    def get_tiles_to_render(self, screen_location, padding=PADDING):

        # Get corners of view in world space
        corners = [
            screen_location.as_world_coord(),
            screen_location.copy().update_as_view_coord(DISPLAY_SIZE[0], 0).as_world_coord(),
            screen_location.copy().update_as_view_coord(0, DISPLAY_SIZE[1]).as_world_coord(),
            screen_location.copy().update_as_view_coord(*DISPLAY_SIZE).as_world_coord(),
        ]

        # Find the bounding box (with padding)
        min_x = math.floor(min(x for x, _ in corners)) - padding
        max_x = math.ceil(max(x for x, _ in corners)) + padding
        min_y = math.floor(min(y for _, y in corners)) - padding
        max_y = math.ceil(max(y for _, y in corners)) + padding

        tiles_to_render = []
        for chunk in self.chunks:
            tiles_to_render.extend(chunk.get_tiles_in_chunk(min_x, max_x, min_y, max_y))

        return tiles_to_render
 
    # setups map with a chunk grid based on location
    def init_map_chunks(self):
        chunk_locations = self.get_chunk_locations()
        self.chunks = [
            Chunk.load(x, y) if self.check_dir_exists(x, y) else Chunk(self.choose_biome(), Coord.chunk(x, y))
            for x, y in chunk_locations
        ]

        for i, chunk in enumerate(self.chunks):
            neighbor_biomes = []
            if len(chunk.tiles) == 0:
                neighbor_biomes.append(self.chunks[i - 3].biome if i - 3 >= 0 else None)       
                neighbor_biomes.append(self.chunks[i + 3].biome if i + 3 < len(self.chunks) else None)
                neighbor_biomes.append(self.chunks[i - 1].biome if i % 3 > 0 else None)
                neighbor_biomes.append(self.chunks[i + 1].biome if i % 3 < 2 else None)
                chunk.generate(neighbor_biomes)
                chunk.save()

    # For now randomly choose a biome
    def choose_biome(self):
        biomes = list(BIOME_TILE_WEIGHTS.keys())
        return biomes[random.randint(0, len(biomes) - 1)]

        
    # Gets all chunk locations
    def get_chunk_locations(self):
        center_x, center_y = self.location.as_chunk_coord()
        return [
            (center_x - 1, center_y + 1),
            (center_x - 1, center_y),
            (center_x - 1, center_y - 1),
            (center_x, center_y + 1),
            (center_x, center_y),
            (center_x, center_y - 1),
            (center_x + 1, center_y + 1),
            (center_x + 1,  center_y),
            (center_x + 1, center_y - 1)
        ]

    @staticmethod
    def check_dir_exists(x, y):
        path = Chunk.get_data_path(x, y)
        return path.is_dir() and any(path.iterdir())
    