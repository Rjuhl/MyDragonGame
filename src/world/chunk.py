import math
import uuid
import json
import pygame
import random
from world.tile import Tile
from pathlib import Path
from utils.paths import data_root
from bisect import bisect_left
from utils.coords import Coord
from system.asset_drawer import AssetDrawer
from constants import CHUNK_SIZE, SEED, TILE_GROUP_DRAW_SIZE, TILES_GEN_PER_STEP, TILES_LOAD_PER_STEP, ENTITY_LOAD_STEP, TOTAL_LOAD_BUDGET 
from world.tile_group import TileGroup
from world.biome_tile_weights import BIOME_TILE_WEIGHTS
from system.id_generator import id_generator
from regestries import ENTITY_REGISTRY, ChunkSpawnerRegistry
from metrics.simple_metrics import timeit
from world.generation.terrain_generator import default_terrain_generator
from typing import Tuple, List





# Chunk Size will be 64 x 64 tiles
class Chunk:
    def __init__(
        self, 
        location, 
        random_number_generator=random.randint, 
        size=CHUNK_SIZE, 
        id=id_generator.get_id(),
        terrain_generator=default_terrain_generator,
        assets=None,
        auto_gen=True
    ):
        self.tiles = []
        self.SIZE = size
        self.location = location
        self.id = id
        self.random_number_generator = random_number_generator
        self.terrain_generator = terrain_generator
        
        self.chunk_spawn_chances = ChunkSpawnerRegistry()
        self.tile_groups = [TileGroup(assets) for _ in range((CHUNK_SIZE // TILE_GROUP_DRAW_SIZE) ** 2)]

        self.entities = []

        self._load_state = None
        self._raw_tile_data = None
        self._raw_entity_data = None
        self._tile_load_index = 0
        self._entity_load_index = 0
        self._group_build_index = 0
        self._assets = assets

        if auto_gen: self.generate()
    
    @classmethod
    @timeit()
    def load(cls, x, y, game_name, assets=None):
        path = next(cls.get_data_path(x, y, game_name).iterdir())
        data = json.loads(path.read_text(encoding='utf-8'))

        chunk_id = data["id"]
        size = int(data["size"])
        location = Coord.load(data["location"])
        tiles = [Tile.load(d) for d in data["tiles"]]
        entities = [ENTITY_REGISTRY.get(e_data["classname"]).load(e_data) for e_data in data["entities"]]

        chunk = cls(location=location, size=size, id=chunk_id, assets=assets, auto_gen=False)
        chunk.tiles = tiles
        chunk.entities = entities

        # Add tiles to tile group
        for i, tile in enumerate(tiles):
            x, y = i // chunk.SIZE, i % chunk.SIZE
            groups_per_row = chunk.SIZE // TILE_GROUP_DRAW_SIZE
            gx = x // TILE_GROUP_DRAW_SIZE
            gy = y // TILE_GROUP_DRAW_SIZE
            tile_group_index = gx * groups_per_row + gy
            chunk.tile_groups[tile_group_index].add_tile(tile)

        return chunk
    

    @classmethod
    def begin_load(cls, x, y, game_name, assets=None):
        path = next(cls.get_data_path(x, y, game_name).iterdir())
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)

        chunk_id = data["id"]
        size = int(data["size"])
        location = Coord.load(data["location"])

        chunk = cls(
            location=location,
            size=size,
            id=chunk_id,
            assets=assets,
            auto_gen=False,
        )

        chunk._load_state = "tiles"
        chunk._raw_tile_data = data["tiles"]
        chunk._raw_entity_data = data["entities"]
        return chunk

    def step_load(self, tile_budget=TILES_LOAD_PER_STEP, entity_budget=ENTITY_LOAD_STEP, group_budget=TOTAL_LOAD_BUDGET):
        if self._load_state == "tiles":
            end = min(self._tile_load_index + tile_budget, len(self._raw_tile_data))
            for i in range(self._tile_load_index, end):
                self.tiles.append(Tile.load(self._raw_tile_data[i]))
            self._tile_load_index = end

            if self._tile_load_index >= len(self._raw_tile_data):
                self._load_state = "entities"

            return False

        if self._load_state == "entities":
            end = min(self._entity_load_index + entity_budget, len(self._raw_entity_data))
            for i in range(self._entity_load_index, end):
                e_data = self._raw_entity_data[i]
                cls = ENTITY_REGISTRY.get(e_data["classname"])
                self.entities.append(cls.load(e_data))
            self._entity_load_index = end

            if self._entity_load_index >= len(self._raw_entity_data):
                self._load_state = "groups"

            return False

        if self._load_state == "groups":
            groups_per_row = self.SIZE // TILE_GROUP_DRAW_SIZE
            end = min(self._group_build_index + group_budget, len(self.tiles))

            for i in range(self._group_build_index, end):
                tile = self.tiles[i]
                x, y = i // self.SIZE, i % self.SIZE
                gx = x // TILE_GROUP_DRAW_SIZE
                gy = y // TILE_GROUP_DRAW_SIZE
                tile_group_index = gx * groups_per_row + gy
                self.tile_groups[tile_group_index].add_tile(tile)

            self._group_build_index = end

            if self._group_build_index >= len(self.tiles):
                self._raw_tile_data = None
                self._raw_entity_data = None
                self._load_state = "done"
                return True

            return False

        return self._load_state == "done"
    
    @timeit()
    def save(self, game_name: str):
        x, y, _ = self.location.as_chunk_coord()
        path = self.get_data_path(x, y, game_name)
        file_path = path / f"{self.id}.chunk"
        file_path.write_text(json.dumps(self.jsonify(), ensure_ascii=False), encoding='utf-8')

    def jsonify(self):
        return {
            "id": self.id,
            "size": self.SIZE,
            "location": self.location.jsonify(),
            "tiles": [tile.jsonify() for tile in self.tiles],
            "entities": [e for entity in self.entities if (e := entity.jsonify())]
        }
    
    def add_entity(self, entity):
        pass

    def remove(self, entity):
        pass
    
    # neighbor_biomes arr -> [left, right, top, bottom] biomes
    @timeit()
    def generate(self):
        if self.random_number_generator is None:
            raise ValueError("random_number_generator must be provided before generating tiles.")

        # Generate tiles in rendering order
        self.tiles = []
        num_tiles = self.SIZE ** 2
        chunk_world_loc = self.location.as_world_coord()
        for i in range(num_tiles):
            x, y = i // self.SIZE, i % self.SIZE
            onborder = (x == 0 or x == self.SIZE - 1 or y == 0 or y == self.SIZE - 1)
            location = Coord.world(chunk_world_loc[0] + x, chunk_world_loc[1] - y)
            tile, entity = self.terrain_generator.generate_tile(location.x, location.y, onborder)
            self.tiles.append(tile)
            if entity: self.entities.append(entity)

            groups_per_row = self.SIZE // TILE_GROUP_DRAW_SIZE
            gx = x // TILE_GROUP_DRAW_SIZE
            gy = y // TILE_GROUP_DRAW_SIZE
            tile_group_index = gx * groups_per_row + gy
            self.tile_groups[tile_group_index].add_tile(tile)
        
        self._generate_chunk_spawners()

    def start_generation(self):
        self.tiles = []
        self.entities = []
        self._gen_index = 0
        self._gen_done = False
        self._groups_per_row = self.SIZE // TILE_GROUP_DRAW_SIZE
        self._chunk_world_loc = self.location.as_world_coord()

    def step_generation(self, tiles_per_step=TILES_GEN_PER_STEP):
        if self._gen_done:
            return True

        end = min(self._gen_index + tiles_per_step, self.SIZE * self.SIZE)

        for i in range(self._gen_index, end):
            x = i // self.SIZE
            y = i % self.SIZE
            onborder = (x == 0 or x == self.SIZE - 1 or y == 0 or y == self.SIZE - 1)

            wx = self._chunk_world_loc[0] + x
            wy = self._chunk_world_loc[1] - y

            tile, entity = self.terrain_generator.generate_tile(wx, wy, onborder)
            self.tiles.append(tile)
            if entity:
                self.entities.append(entity)

            gx = x // TILE_GROUP_DRAW_SIZE
            gy = y // TILE_GROUP_DRAW_SIZE
            tile_group_index = gx * self._groups_per_row + gy
            self.tile_groups[tile_group_index].add_tile(tile)

        self._gen_index = end

        if self._gen_index >= self.SIZE * self.SIZE:
            self._generate_chunk_spawners()
            self._gen_done = True
            return True

        return False
    
    def get_tile(self, location: Coord) -> Tile | None:
        if not self.contains_coord(location): return None
        location = location.copy()
        location -= Coord.chunk(*location.as_chunk_coord())

        x, y = int(location.x), int(abs(location.y)) % self.SIZE
        return self.tiles[x * self.SIZE + y]
    

    def _generate_chunk_spawners(self) -> None:
        entities_spawned = 0
        for tile in self.tiles:
            if (e_type := self.chunk_spawn_chances.choose_random_type()):
                tiles_to_check = [
                    self.get_tile(tile.location.copy().update_as_world_coord(x, -y))
                    for x in range(int(e_type.SIZE.x))
                    for y in range(int(e_type.SIZE.y))
                ]
                if all([tile is not None and e_type.CAN_SPAWN_SPAWNER(tile) for tile in tiles_to_check]):
                    self.entities.append(e_type(tile))
                    entities_spawned += 1
                    for tile in tiles_to_check: tile.has_obsticle = True


    def contains_coord(self, coord):
        new_coord = self.location.copy().update_as_chunk_coord(1, -1)
        return self.location.x <= coord.x < new_coord.x and \
               new_coord.y < coord.y <= self.location.y


    def get_tiles(self):
        return self.tiles


    def get_tiles_in_chunk(self, world_row_start, world_row_end, world_col_start, world_col_end):
        chunk_wx, chunk_wy, _ = self.location.as_world_coord()

        x_min = chunk_wx
        x_max = chunk_wx + self.SIZE - 1
        y_min = chunk_wy - self.SIZE + 1
        y_max = chunk_wy

        if any([
            world_row_start > x_max,
            world_row_end < x_min,
            world_col_start > y_max,
            world_col_end < y_min,
            world_row_start > world_row_end,
            world_col_start > world_col_end
        ]): return []

        if all([
            world_row_start <= x_min <= world_row_end,
            world_row_start <= x_max <= world_row_end,
            world_col_start <= y_min <= world_col_end,
            world_col_start <= y_max <= world_col_end
        ]): return self.get_tiles()

        local_row_min = max(world_row_start - chunk_wx, 0) 
        local_row_max = min(world_row_end - chunk_wx, self.SIZE)
        local_col_min = -min(world_col_end - chunk_wy, 0) 
        local_col_max = -max(world_col_start - chunk_wy, -self.SIZE) 

        tiles_on_screen = []
        for row in range(local_row_min, local_row_max):
            startIdx = row * self.SIZE
            tiles_on_screen.extend(self.tiles[startIdx + local_col_min: startIdx + local_col_max + 1])

        return tiles_on_screen

    def get_tile_groups_in_region(self, region: Tuple[Coord, Coord]) -> List[Tuple[pygame.Surface, Tuple[int, int]]]:
        tile_group_surfaces = []
        for tile_group in self.tile_groups:
            if (tile_group_surface := tile_group.get_surface(region)):
                tile_group_surfaces.append(tile_group_surface)
        return tile_group_surfaces
    

    @staticmethod
    def get_data_path(x, y, game_name: str):
        full_path = data_root() / 'games' / game_name / 'chunks' / f'{x}' / f'{y}'
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    @staticmethod
    def weight_decay(weight, distance):
        return weight * 2 * (math.e ** (-distance))
    
