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
from typing import Optional, Tuple, List
from pathlib import Path
from world.path_finder import path_finder
from metrics.simple_metrics import timeit

from functools import lru_cache

# Updates chunk list based on player location
# Chunk ordering:
#     1   4   7
#     2   5   8
#     3   6   9


class Map:
    def __init__(self, game_name, screen, player, terrain_generator, assets=None):
        self.game_name = game_name
        self.chunks = []
        self.player = None
        self.screen = screen
        self.entity_manager = EntityManager(self.screen)
        self.entities_to_render = []
        self.terrain_generator = terrain_generator
        self.assets = assets

        self.bind_player(player)

        self.chunk_center = self.screen.get_screen_center().as_chunk_coord()
        self.init_map_chunks()

        path_finder.bind_map(self)

        # ---- Load chunks over a few frames ---- #        
        self._is_loading_chunks: bool = False
        self._loading_chunks: List[Optional[Chunk]] = [None] * 9

        self._chunk_loading: Optional[Tuple[int, Chunk]] = None
        self._chunk_generating: Optional[Tuple[int, Chunk]] = None
        self._chunks_to_save: set[int] = []
        self._chunks_to_load: List[Tuple[int, Tuple[int, int]]] = []
        self._chunks_to_generate: List[Tuple[int, Tuple[int, int]]] = []

    def bind_player(self, player):
        self.player = player
        self.screen.anchor = player
        self.screen.center_anchor()
        self.entity_manager.set_player(player)
        self.entity_manager.add_entity(player)


    def unbind_player(self):
        self.entity_manager.set_player(None)
        self.entity_manager.remove_entity(self.player)
        self.player = None
        self.screen.anchor = Entity.dummy()
        self.screen.center_anchor()
        
    def update(self):
        self.handle_chunk_loading()
        path_finder.run_jobs()
        self.entity_manager.update_entities()
        self.player.smooth_movement()
        self.screen.update()
        self.entities_to_render = self.entity_manager.get_entity_render_objs(self.player)
        

    def get_tiles_to_render(self, min_x, max_x, min_y, max_y):

        tiles_to_render = []
        for chunk in self.chunks:
            tiles_to_render.extend(chunk.get_tiles_in_chunk(min_x, max_x, min_y, max_y))

        return tiles_to_render
    
    def get_tile_surfaces_to_render(self, min_x, max_x, min_y, max_y):
        tile_surfaces_to_render = []
        region = (
            Coord.world(min_x, min_y),
            Coord.world(max_x - min_x, max_y - min_y, 1) 
        )

        for chunk in self.chunks:
            tile_surfaces_to_render.extend(chunk.get_tile_groups_in_region(region))

        return tile_surfaces_to_render

    
    @timeit()
    def handle_chunk_loading(self):
        if np.array_equal(
            self.chunk_center,
            self.screen.get_screen_center().as_chunk_coord()
        ) and not self._is_loading_chunks: return
        
        if not self._is_loading_chunks:
            self._is_loading_chunks = True
            self.chunk_center = self.screen.get_screen_center().as_chunk_coord()
            chunks_reused = set()

            for i, (x, y) in enumerate(self.get_chunk_locations()):
                if (c_indx := self.get_chunk_index(self.chunks, Coord.chunk(x, y))):
                    # new chunk location is in previous chunks list
                    self._loading_chunks[i] = self.chunks[c_indx - 1]
                    chunks_reused.add(c_indx - 1)                    
                else: 
                    if self.check_dir_exists(x, y):
                        self._chunks_to_load.append((i, (x, y)))
                    else: self._chunks_to_generate.append((i, (x, y)))

            self._chunks_to_save = set(range(9)) - chunks_reused
                    
                
        if self._handle_saving_queue(): return
        if self._handle_loading_queue(): return
        if self._handle_generation_queue(): return

        self.chunks = self._loading_chunks
        self._reset_chunk_loading()
        path_finder.clear_cache()

    def _handle_saving_queue(self) -> bool:
        if len(self._chunks_to_save) > 0:
            chunk = self.chunks[self._chunks_to_save.pop()]
            chunk.entities = list(self.entity_manager.get_and_removed_chunk_entities(chunk))
            chunk.save(self.game_name)
            return True
        return False
    
    def _handle_loading_queue(self):
        if len(self._chunks_to_load) > 0 or self._chunk_loading:
            if not self._chunk_loading:
                index, (x, y) = self._chunks_to_load.pop()
                self._chunk_loading = (index, Chunk.begin_load(x, y, self.game_name, assets=self.assets))
            
            if self._chunk_loading[1].step_load():
                self._loading_chunks[self._chunk_loading[0]] = self._chunk_loading[1]
                self._chunk_loading = None
                return len(self._chunks_to_load) > 0
            return True
        return False
    
    def _handle_generation_queue(self):
        if len(self._chunks_to_generate) > 0 or self._chunk_generating:
            if not self._chunk_generating:
                index, (x, y) = self._chunks_to_generate.pop()
                self._chunk_generating = (index, Chunk(
                    Coord.chunk(x, y), 
                    terrain_generator=self.terrain_generator,
                    assets=self.assets,
                    auto_gen=False
                ))
                self._chunk_generating[1].start_generation()

            if self._chunk_generating[1].step_generation():
                self._loading_chunks[self._chunk_generating[0]] = self._chunk_generating[1]
                self._chunk_generating = None
                return len(self._chunks_to_generate) > 0
            
            return True
        return False
    
    def _reset_chunk_loading(self):
        self._is_loading_chunks: bool = False
        self._chunks_to_save = []
        self._chunks_to_load = []
        self._chunks_to_generate = []
        self._loading_chunks = [None] * 9

    # setups map with a chunk grid based on location
    def init_map_chunks(self):
        chunk_locations = self.get_chunk_locations()
        self.chunks = [
            Chunk.load(x, y, self.game_name, assets=self.assets) if self.check_dir_exists(x, y) else Chunk(Coord.chunk(x, y), terrain_generator=self.terrain_generator, assets=self.assets)
            for x, y in chunk_locations
        ]

        for chunk in self.chunks:
            for entity in chunk.entities: 
                self.entity_manager.add_entity(entity)

    def generate_loaded_chunks(self):
        for i, chunk in enumerate(self.chunks):
            neighbor_biomes = []
            if len(chunk.tiles) == 0:
                neighbor_biomes.append(self.chunks[i - 3].biome if i - 3 >= 0 else None)       
                neighbor_biomes.append(self.chunks[i + 3].biome if i + 3 < len(self.chunks) else None)
                neighbor_biomes.append(self.chunks[i - 1].biome if i % 3 > 0 else None)
                neighbor_biomes.append(self.chunks[i + 1].biome if i % 3 < 2 else None)
                chunk.generate(neighbor_biomes)
                chunk.save(self.game_name)

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
        

    def save(self):
        while self._is_loading_chunks: self.handle_chunk_loading()
        for chunk in self.chunks: 
            chunk.entities = list(self.entity_manager.get_chunk_entities(chunk))
            chunk.save(self.game_name)
            

    def check_dir_exists(self, x, y):
        path = Chunk.get_data_path(x, y, self.game_name)
        return path.is_dir() and any(path.iterdir())
    
    @staticmethod
    def get_chunk_index(chunk_list, location):
        for i, chunk in enumerate(chunk_list):
            if np.array_equal(
                location.as_chunk_coord(),
                chunk.location.as_chunk_coord()
            ): return i + 1
        return None
