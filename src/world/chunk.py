import math
import uuid
import random
from world.tile import Tile
from pathlib import Path
from bisect import bisect_left
from utils.coords import Coord
from constants import CHUNK_SIZE
from world.biome_tile_weights import BIOME_TILE_WEIGHTS

# Chunk Size will be 128 x 128 tiles
class Chunk:
    delimiter = "|"

    def __init__(self, biome, location, random_number_generator=random.randint, size=CHUNK_SIZE):
        self.tiles = []
        self.SIZE = size
        self.biome = biome
        self.location = location
        self.id = str(uuid.uuid4())
        self.random_number_generator = random_number_generator
    
    @classmethod
    def load(cls, x, y):
        path = next(cls.get_data_path(x, y).iterdir())
        data = path.read_text(encoding='utf-8').split(cls.delimiter)

        chunk_id = data[0]
        biome = data[1]
        size = int(data[2])
        location = Coord.chunk(int(data[3]), int(data[4]))
        tiles = [Tile.load(d) for d in data[5:]]

        chunk = cls(biome=biome, location=location, size=size)
        chunk.id = chunk_id
        chunk.tiles = tiles
        return chunk
    
    def save(self):
        x, y = self.location.as_chunk_coord()
        path = self.get_data_path(x, y)
        file_path = path / f"{self.id}.chunk"
        base = f"{self.id}{self.delimiter}{self.biome}{self.delimiter}{self.SIZE}{self.delimiter}{x}{self.delimiter}{y}"
        serialization = [base] + [str(tile) for tile in self.tiles]
        file_path.write_text(self.delimiter.join(serialization), encoding='utf-8')
    
    # neighbor_biomes arr -> [left, right, top, bottom] biomes
    def generate(self, neighbor_biomes):
        if self.random_number_generator is None:
            raise ValueError("random_number_generator must be provided before generating tiles.")

        # Generate tiles in rendering order
        self.tiles = []
        num_tiles = self.SIZE ** 2
        for i in range(num_tiles):
            x, y = i // self.SIZE, i % self.SIZE
            self.tiles.append(self.generate_tile(x, y, neighbor_biomes))
        
    
    def generate_tile(self, x, y, neighbor_biomes, round_factor=100):
        prefix_sum, ids = [], []
        current_sum = 0
        for id, weight in BIOME_TILE_WEIGHTS[self.biome]:
            current_sum += weight * round_factor
            ids.append(id)
            prefix_sum.append(current_sum)
        
        for b, biome in enumerate(neighbor_biomes):
            if biome is None: continue
            for id, weight in BIOME_TILE_WEIGHTS[biome]:
                current_sum += math.floor(self.weight_decay(weight, self.get_distance(x, y, b)) * round_factor)
                ids.append(id)
                prefix_sum.append(current_sum)

        random_tile = self.random_number_generator(0, math.floor(current_sum))
        chunk_world_loc = self.location.as_world_coord()
        location = Coord.world(chunk_world_loc[0] + x, chunk_world_loc[1] - y)
        return Tile(ids[bisect_left(prefix_sum, random_tile)], location)
    
    def get_distance(self, x, y, biome):
        if biome == 0: return x
        if biome == 1: return self.SIZE - x 
        if biome == 2: return y
        if biome == 3: return self.SIZE - y
        else: return 0
    
    def contains_coord(self, coord):
        new_coord = coord.copy()
        new_coord.update_as_chunk_coord(1, -1)
        return self.location.x <= coord.x <= new_coord.x and \
               new_coord.y <= coord.y <= self.location.x


    def get_tiles(self):
        return self.tiles


    def get_tiles_in_chunk(self, world_row_start, world_row_end, world_col_start, world_col_end):
        chunk_wx, chunk_wy = self.location.as_world_coord()

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
    def get_data_path(x, y):
        current_dir = Path(__file__).parent
        full_path = current_dir.parent.parent / 'data' / 'chunks' / f'{x}' / f'{y}'
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    @staticmethod
    def weight_decay(weight, distance):
        return weight * 2 * (math.e ** (-distance))
    
