import math
import uuid
import json
import random
from world.tile import Tile
from pathlib import Path
from bisect import bisect_left
from utils.coords import Coord
from constants import CHUNK_SIZE, SEED
from world.biome_tile_weights import BIOME_TILE_WEIGHTS
from system.id_generator import id_generator
from regestries import ENTITY_REGISTRY, ChunkSpawnerRegistry
from world.generation.terrain_generator import default_terrain_generator

# Chunk Size will be 64 x 64 tiles
class Chunk:
    def __init__(
        self, 
        location, 
        random_number_generator=random.randint, 
        size=CHUNK_SIZE, 
        id=id_generator.get_id(),
        terrain_generator=default_terrain_generator
    ):
        self.tiles = []
        self.SIZE = size
        self.location = location
        self.id = id
        self.random_number_generator = random_number_generator
        self.terrain_generator = terrain_generator
        
        self.chunk_spawn_chances = ChunkSpawnerRegistry()

        self.entities = []
        self.generate()
    
    @classmethod
    def load(cls, x, y, game_name):
        path = next(cls.get_data_path(x, y, game_name).iterdir())
        data = json.loads(path.read_text(encoding='utf-8'))

        chunk_id = data["id"]
        size = int(data["size"])
        location = Coord.load(data["location"])
        tiles = [Tile.load(d) for d in data["tiles"]]
        entities = [ENTITY_REGISTRY.get(e_data["classname"]).load(e_data) for e_data in data["entities"]]

        chunk = cls(location=location, size=size, id=chunk_id)
        chunk.tiles = tiles
        chunk.entities = entities

        return chunk
    
    def save(self, game_name: str):
        x, y, _ = self.location.as_chunk_coord()
        path = self.get_data_path(x, y, game_name)
        file_path = path / f"{self.id}.chunk"
        file_path.write_text(json.dumps(self.jsonify(), ensure_ascii=False, indent=2), encoding='utf-8')

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
        
        self._generate_chunk_spawners()
    
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
    

    @staticmethod
    def get_data_path(x, y, game_name: str):
        current_dir = Path(__file__).parent
        full_path = current_dir.parent.parent / 'data' / 'games' / game_name / 'chunks' / f'{x}' / f'{y}'
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    @staticmethod
    def weight_decay(weight, distance):
        return weight * 2 * (math.e ** (-distance))
    
