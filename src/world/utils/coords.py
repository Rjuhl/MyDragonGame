import numpy as np
from constants import CHUNK_SIZE

class Coord:
    DELIMITER = "#"

    BASIS = np.array([
        [16, 16],
        [8, -8]
    ], dtype=np.float64)

    INV_BASIS = np.linalg.inv(BASIS)

    def __init__(self):
        raise RuntimeError("Initialize with classmethod: world, view, or chunk.")

    @classmethod
    def world(cls, x, y):
        instance = object.__new__(cls)
        instance.location = np.array([x, y], dtype=np.float64)  # float64 now
        return instance

    @classmethod
    def view(cls, vx, vy, screen_offset):
        # Convert view coords to world coords using screen offset
        screen = np.array([vx, vy], dtype=np.float64) + (Coord.BASIS @ screen_offset.location)
        world_coords = Coord.INV_BASIS @ screen
        return cls.world(world_coords[0], world_coords[1])

    @classmethod
    def chunk(cls, x, y):
        return cls.world(x * CHUNK_SIZE, y * CHUNK_SIZE)

    @classmethod
    def load(cls, data):
        data = data.split(cls.DELIMITER)
        return cls.world(float(data[0]), float(data[1]))

    def as_world_coord(self):
        return self.location.astype(int)

    def as_view_coord(self, screen_offset):
        screen_pos = Coord.BASIS @ self.location
        screen_offset_pos = Coord.BASIS @ screen_offset.location
        return (screen_pos - screen_offset_pos).astype(int)

    def as_chunk_coord(self):
        return (self.location / CHUNK_SIZE).astype(int)

    def update_as_world_coord(self, dx, dy):
        delta = np.array([dx, dy], dtype=np.float64)
        self.location += delta
        return self

    def update_as_view_coord(self, dx, dy):
        delta_world = Coord.INV_BASIS @ np.array([dx, dy], dtype=np.float64)
        self.location += delta_world
        return self

    def update_as_chunk_coord(self, dx, dy):
        delta = np.array([dx, dy], dtype=np.float64) * CHUNK_SIZE
        self.location += delta
        return self

    def copy(self):
        return Coord.world(*self.as_world_coord())

    def __hash__(self):
        return hash((self.location[0], self.location[1]))

    def __str__(self):
        loc_x, loc_y = self.location.tolist()
        return f"{loc_x}{self.DELIMITER}{loc_y}"

    def __eq__(self, other):
        if not isinstance(other, Coord):
            return NotImplemented
        return np.allclose(self.location, other.location)

    def __add__(self, other):
        if isinstance(other, Coord):
            return Coord.world(
                self.location[0] + other.location[0],
                self.location[1] + other.location[1]
            )
        if isinstance(other, tuple) and len(other) == 2:
            return Coord.world(
                self.location[0] + other[0],
                self.location[1] + other[1]
            )
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Coord):
            return Coord.world(
                self.location[0] - other.location[0],
                self.location[1] - other.location[1]
            )
        if isinstance(other, tuple) and len(other) == 2:
            return Coord.world(
                self.location[0] - other[0],
                self.location[1] - other[1]
            )
        return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, Coord):
            self.location += other.location
            return self
        if isinstance(other, tuple) and len(other) == 2:
            self.location += np.array(other, dtype=np.float64)
            return self
        return NotImplemented

    def __isub__(self, other):
        if isinstance(other, Coord):
            self.location -= other.location
            return self
        if isinstance(other, tuple) and len(other) == 2:
            self.location -= np.array(other, dtype=np.float64)
            return self
        return NotImplemented
