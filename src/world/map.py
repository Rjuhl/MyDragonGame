import math
import random
from pygame.locals import *
from utils.coords import Coord
from world.chunk import Chunk
from world.biome_tile_weights import BIOME_TILE_WEIGHTS
from system.entities.entity_manager import EntityManager
from constants import DISPLAY_SIZE, PADDING

# Updates chunk list based on player location
# Chunk ordering:
#     1   4   7
#     2   5   8
#     3   6   9


class Map:

    def __init__(self, screen):
        self.chunks = []
        self.screen = screen
        self.entity_manager = EntityManager(self.screen)
        self.init_map_chunks()
    
    # TODO: Needs to update location. If locations crosses to new chunk, load new chunks
    def update_location(self, dx, dy):
        pass

    def get_tiles_to_render(self, min_x, max_x, min_y, max_y):

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
        center_x, center_y, _ = self.screen.coord.as_chunk_coord()
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
    