import math
import random
import numpy as np
from pygame.locals import *
from utils.coords import Coord
from world.chunk import Chunk
from world.biome_tile_weights import BIOME_TILE_WEIGHTS
from system.entities.entity import Entity
from system.entities.entity_manager import EntityManager
from constants import DISPLAY_SIZE, PADDING
from system.entities.sprites.tree import Tree
from system.game_clock import game_clock

# Updates chunk list based on player location
# Chunk ordering:
#     1   4   7
#     2   5   8
#     3   6   9


class Map:

    def __init__(self, screen):
        self.chunks = []
        self.player = None
        self.screen = screen
        self.entity_manager = EntityManager(self.screen)

        self.chunk_center = self.screen.get_screen_center().as_chunk_coord()
        self.init_map_chunks()

    def bind_player(self, player):
        self.player = player
        self.screen.anchor = player
        self.screen.center_anchor()

    def unbind_player(self):
        self.player = None
        self.screen.anchor = Entity.dummy()
        self.screen.center_anchor()

    def update_entities(self):
        self.player.update(game_clock.dt)

    def update(self):
        self.handle_chunk_loading()
        self.update_entities()
        self.screen.update()

    def get_tiles_to_render(self, min_x, max_x, min_y, max_y):

        tiles_to_render = []
        for chunk in self.chunks:
            tiles_to_render.extend(chunk.get_tiles_in_chunk(min_x, max_x, min_y, max_y))

        return tiles_to_render
    
    
    # TODO: Add entity loading/unloading here or in a similiar fashion
    def handle_chunk_loading(self):
        if np.array_equal(
            self.chunk_center,
            self.screen.get_screen_center().as_chunk_coord()
        ): return
        self.chunk_center = self.screen.get_screen_center().as_chunk_coord()

        chunks = []
        new_locations = self.get_chunk_locations()
        chunks_not_to_save = []
        for i, (x, y) in enumerate(new_locations):
            if (index := self.get_chunk_index(self.chunks, Coord.chunk(x, y))):
                chunks.append(self.chunks[index - 1])
                chunks_not_to_save.append(index - 1)
            elif self.check_dir_exists(x, y):
                chunks.append(Chunk.load(x, y))
            else:
                chunks.append(Chunk(self.choose_biome(), Coord.chunk(x, y)))
        
        for i, chunk in enumerate(self.chunks):
            if i not in chunks_not_to_save: chunk.save()
        
        self.chunks = chunks
        self.generate_loaded_chunks()
 
    # setups map with a chunk grid based on location
    def init_map_chunks(self):
        chunk_locations = self.get_chunk_locations()
        self.chunks = [
            Chunk.load(x, y) if self.check_dir_exists(x, y) else Chunk(self.choose_biome(), Coord.chunk(x, y))
            for x, y in chunk_locations
        ]

        self.generate_loaded_chunks()

    def generate_loaded_chunks(self):
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
        center_x, center_y, _ = self.chunk_center
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

    # TODO: implement this
    def get_entities_to_render(self):
        E =  [Tree(Coord.world(1, 0)), Tree(Coord.world(2, 0)), Tree(Coord.world(14, -8))]
        # E = []
        if self.player: E.append(self.player)

        # for e in E: e.update(game_clock.dt)

        return E
    

    @staticmethod
    def check_dir_exists(x, y):
        path = Chunk.get_data_path(x, y)
        return path.is_dir() and any(path.iterdir())
    
    @staticmethod
    def get_chunk_index(chunk_list, location):
        for i, chunk in enumerate(chunk_list):
            if np.array_equal(
                location.as_chunk_coord(),
                chunk.location.as_chunk_coord()
            ): return i + 1
        return None
