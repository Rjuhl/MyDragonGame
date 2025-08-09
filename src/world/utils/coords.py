import numpy as np
from constants import CHUNK_SIZE

class Coord:
    DELIMITER = "#"

    BASIS = np.array([
        [16, 16],
        [8, -8]
    ])
    INV_BASIS = np.linalg.inv(BASIS)

    def __init__(self):
        raise RuntimeError("Initialize with classmethod: world, view, or chunk.")

    @classmethod
    def world(cls, x, y):
        instance = object.__new__(cls)
        instance.location = np.array([int(x), int(y)], dtype=np.int32)
        return instance

    @classmethod
    def view(cls, vx, vy, screen_offset):
        # Convert view coords to world coords using screen offset
        screen = np.array([vx, vy], dtype=float) + (Coord.BASIS @ screen_offset.location)
        world_coords = np.round(Coord.INV_BASIS @ screen).astype(np.int32)
        return cls.world(world_coords[0], world_coords[1])

    @classmethod
    def chunk(cls, x, y):
        return cls.world(x * CHUNK_SIZE, y * CHUNK_SIZE)
    
    @classmethod
    def load(cls, data):
        data = data.split(cls.DELIMITER)
        return cls.world(int(data[0]), int(data[1]))

    def as_world_coord(self):
        return tuple(self.location)

    def as_view_coord(self, screen_offset):
        screen_pos = Coord.BASIS @ self.location
        screen_offset_pos = Coord.BASIS @ screen_offset.location
        return tuple((screen_pos - screen_offset_pos).astype(int))

    def as_chunk_coord(self):
        return (self.location[0] // CHUNK_SIZE, self.location[1] // CHUNK_SIZE)

    def update_as_world_coord(self, dx, dy):
        delta = np.array([int(dx), int(dy)], dtype=np.int32)
        self.location += delta
        return self

    def update_as_view_coord(self, dx, dy):
        delta_world = Coord.INV_BASIS @ np.array([dx, dy], dtype=float)
        self.location += np.round(delta_world).astype(np.int32)
        return self
    
    def update_as_chunk_coord(self, dx, dy):
        delta = np.array([dx, dy]) * CHUNK_SIZE
        self.location += np.round(delta).astype(np.int32)
        return self
    
    def copy(self):
        return Coord.world(*self.as_world_coord())

    def __eq__(self, other):
        if not isinstance(other, Coord):
            return NotImplemented
        return np.array_equal(self.location, other.location)

    def __hash__(self):
        return hash((self.location[0], self.location[1]))

    def __str__(self):
        loc_x, loc_y = self.location.tolist()
        return f"{loc_x}{self.DELIMITER}{loc_y}"