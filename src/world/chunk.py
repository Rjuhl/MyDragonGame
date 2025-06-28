import math
import uuid
from tile import Tile
from pathlib import Path
from bisect import bisect_left
from biome_tile_weights import BIOME_TILE_WEIGHTS

# Chunk Size will be 128 x 128 tiles
class Chunk:
    delimiter = "|"

    def __init__(self, biome, location, random_number_generator=None, size=128):
        self.tiles = []
        self.SIZE = size
        self.biome = biome
        self.location = location
        self.id = str(uuid.uuid4())
        self.random_number_generator = random_number_generator
    
    @classmethod
    def load(cls, path):
        data = path.read_text(encoding='utf-8').split(cls.delimiter)

        chunk_id = data[0]
        biome = data[1]
        size = int(data[2])
        location = (int(data[3]), int(data[4]))
        tiles = [Tile.load(d) for d in data[5:]]

        chunk = cls(biome=biome, location=location, size=size)
        chunk.id = chunk_id
        chunk.tiles = tiles
        return chunk
    
    def save(self):
        x, y = self.location
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
        for i in range(self.SIZE * self.SIZE):
            x, y = i // self.SIZE, i % self.SIZE
            self.tiles.append(self.generate_tile(x, y, neighbor_biomes))

    
    def generate_tile(self, x, y, neighbor_biomes):
        prefix_sum, ids = [], []
        current_sum = 0
        for id, weight in BIOME_TILE_WEIGHTS[self.biome]:
            current_sum += weight
            ids.append(id)
            prefix_sum.append(current_sum)
        
        for b, biome in enumerate(neighbor_biomes):
            for id, weight in BIOME_TILE_WEIGHTS[biome]:
                current_sum += self.weight_decay(weight, self.get_distance(x, y, b))
                ids.append(id)
                prefix_sum.append(current_sum)
        
        random_tile = self.random_number_generator(0, current_sum)
        return Tile(ids[bisect_left(prefix_sum, random_tile)])
    
    def get_distance(self, x, y, biome):
        if biome == 0: return x
        if biome == 1: return self.SIZE - x - 1
        if biome == 2: return y
        if biome == 3: return self.SIZE - y - 1
        else: return 0

    # TODO 
    def get_tile(self, x, y):
        pass

    @staticmethod
    def get_data_path(x, y):
        current_dir = Path(__file__).parent
        full_path = current_dir.parent.parent / 'data' / 'chunks' / f'{x}' / f'{y}'
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    @staticmethod
    def weight_decay(weight, distance):
        return weight * 2 * (math.e ** -distance)
