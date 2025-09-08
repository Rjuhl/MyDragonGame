import numpy as np
from constants import CHUNK_SIZE

class Coord:
    DELIMITER = "#"

    BASIS = np.array([
        [16, 16, 0],
        [8, -8, 0],
        [0, 0, 1]
    ], dtype=np.float64)

    INV_BASIS = np.linalg.inv(BASIS)

    def __init__(self, location):
        self.location = location.astype(np.float64)

     # --- x, y, z always reflect/self-update location (in world coords) ---
    @property
    def x(self): return float(self.location[0])
    @x.setter
    def x(self, v): self.location[0] = float(v)

    @property
    def y(self): return float(self.location[1])
    @y.setter
    def y(self, v): self.location[1] = float(v)

    @property
    def z(self): return float(self.location[2])
    @z.setter
    def z(self, v): self.location[2] = float(v)

    @classmethod
    def world(cls, x, y, z=0):
        instance = object.__new__(cls)
        instance.location = np.array([x, y, z], dtype=np.float64)
        return instance

    @classmethod
    def view(cls, vx, vy, vz, cam_offset):
        # Convert view coords to world coords using screen offset
        screen = np.array([vx, vy, vz], dtype=np.float64) - cam_offset
        world_coords = Coord.INV_BASIS @ screen
        return Coord(world_coords)

    @classmethod
    def chunk(cls, x, y, z=0):
        return cls.world(x * CHUNK_SIZE, y * CHUNK_SIZE, z)
    
    @classmethod
    def math(cls, x, y, z):
        return cls.world(x, y, z)

    @classmethod
    def load(cls, data):
        data = data.split(cls.DELIMITER)
        return cls.world(float(data[0]), float(data[1]))

    def as_world_coord(self):
        return np.floor(self.location).astype(int)

    def as_view_coord(self, screen_offset=None, cam_offset=None):
        screen_pos = Coord.BASIS @ self.location
        screen_offset_pos = Coord.BASIS @ screen_offset.location if cam_offset is None else cam_offset
        return (np.floor(screen_pos - screen_offset_pos)).astype(int)[:-1]
       

    def as_chunk_coord(self):
        # Floor x, ceil y, and floor z if present
        loc = self.location / CHUNK_SIZE
        x = np.floor(loc[0]).astype(int)
        y = np.ceil(loc[1]).astype(int)
        if len(loc) > 2:
            z = np.floor(loc[2]).astype(int)
            return np.array([x, y, z])
        return np.array([x, y])

    def update_as_world_coord(self, dx, dy, dz=0):
        delta = np.array([dx, dy, dz], dtype=np.float64)
        self.location += delta
        return self

    def update_as_view_coord(self, dx, dy, dz=0):
        delta_world = Coord.INV_BASIS @ np.array([dx, dy, dz], dtype=np.float64) 
        self.location += delta_world
        return self
    
    
    def normalize_in_screen_space(self):
        cam_screen = Coord.BASIS @ self.location 
        cam_screen_i = np.floor(cam_screen + 1e-9)
        self.location = Coord.INV_BASIS @ cam_screen_i

        return self

    def update_as_chunk_coord(self, dx, dy, dz=0):
        delta = np.array([dx, dy, dz], dtype=np.float64) * CHUNK_SIZE
        self.location += delta
        return self

    def copy(self):
        return Coord.world(*self.location)

    def __hash__(self):
        return hash((self.location[0], self.location[1], self.location[2]))

    def __str__(self):
        loc_x, loc_y, loc_z = self.location.tolist()
        return f"{loc_x}{self.DELIMITER}{loc_y}{self.DELIMITER}{loc_z}"

   # --- helpers for arithmetic ---
    @staticmethod
    def _coerce(other) -> np.ndarray:
        if isinstance(other, Coord):
            return other.location
        if np.isscalar(other):
            return np.array([other, other, other], dtype=np.float64)
        a = np.asarray(other, dtype=np.float64)
        if a.shape != (3,):
            raise TypeError("Expected coord, scalar, or array-like of length 3")
        return a

    # --- arithmetic (new object) ---
    def __add__(self, other):      return Coord(self.location + self._coerce(other))
    def __sub__(self, other):      return Coord(self.location - self._coerce(other))
    def __mul__(self, other):      return Coord(self.location * self._coerce(other))
    def __truediv__(self, other):  return Coord(self.location / self._coerce(other))

    # --- reflected arithmetic ---
    def __radd__(self, other):     return self.__add__(other)
    def __rsub__(self, other):     return Coord(self._coerce(other) - self.location)
    def __rmul__(self, other):     return self.__mul__(other)
    def __rtruediv__(self, other): return Coord(self._coerce(other) / self.location)

    # --- in-place arithmetic ---
    def __iadd__(self, other):     self.location += self._coerce(other); return self
    def __isub__(self, other):     self.location -= self._coerce(other); return self
    def __imul__(self, other):     self.location *= self._coerce(other); return self
    def __itruediv__(self, other): self.location /= self._coerce(other); return self

    # --- equality (float-friendly) ---
    def __eq__(self, other) -> bool:
        try:
            return bool(np.allclose(self.location, self._coerce(other)))
        except TypeError:
            return NotImplemented
