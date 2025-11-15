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
from system.entities.spawners.fox_burrow import FoxBurrow
from system.entities.sprites.fox import Fox
from world.tile import Tile
from typing import Optional

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
        self.entities_to_render = []

        self.chunk_center = self.screen.get_screen_center().as_chunk_coord()
        self.init_map_chunks()

        # TEMP for testing
        E = [Fox(Coord.world(1, 0), None)]
        for e in E: self.entity_manager.add_entity(e)

    def bind_player(self, player):
        self.player = player
        self.screen.anchor = player
        self.screen.center_anchor()
        self.entity_manager.add_entity(player)


    def unbind_player(self):
        self.entity_manager.remove_entity(self.player)
        self.player = None
        self.screen.anchor = Entity.dummy()
        self.screen.center_anchor()
        
    def update(self):
        self.handle_chunk_loading()
        self.entity_manager.update_entities()
        self.player.smooth_movement()
        self.screen.update()
        self.entities_to_render = self.entity_manager.get_entity_render_objs(self.player)

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
            # If chunk is still loaded
            if (index := self.get_chunk_index(self.chunks, Coord.chunk(x, y))):
                chunks.append(self.chunks[index - 1])
                chunks_not_to_save.append(index - 1)

            else:
                chunk = Chunk.load(x, y) if self.check_dir_exists(x, y) else Chunk(self.choose_biome(), Coord.chunk(x, y))
                chunks.append(chunk)
                for entity in chunk.entities: 
                    self.entity_manager.add_entity(entity)
        
        for i, chunk in enumerate(self.chunks):
            if i not in chunks_not_to_save: 
                # First remove entities from manager and add them to chunk to save
                chunk.entities = self.entity_manager.get_and_removed_chunk_entities(chunk)
                chunk.save()
               
        self.chunks = chunks
 
    # setups map with a chunk grid based on location
    def init_map_chunks(self):
        chunk_locations = self.get_chunk_locations()
        self.chunks = [
            Chunk.load(x, y) if self.check_dir_exists(x, y) else Chunk(self.choose_biome(), Coord.chunk(x, y))
            for x, y in chunk_locations
        ]

        for chunk in self.chunks:
            for entity in chunk.entities: self.entity_manager.add_entity(entity)

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

    def get_entities_to_render(self):
        return self.entities_to_render
    
    def get_tile(self, coord: Coord) -> Optional[Tile]:
        for chunk in self.chunks:
            if chunk.contains_coord(coord): return chunk.get_tile(coord)

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
