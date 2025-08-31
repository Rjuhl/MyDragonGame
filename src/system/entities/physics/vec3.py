import numpy as np
from typing import Iterable, Union
from utils.coords import Coord

Number = Union[int, float, np.number]

class Vec3:
    DELIMITER = "!"
    __slots__ = ("_loc",)  # no __dict__; store only the underlying array

    def __init__(self, v: Union[Iterable[Number], Coord]):
        self.location = v.append(0).as_type(np.float64) if isinstance(v, Coord) else v.as_type(np.float64)

    # --- location stored in _loc; expose as a property ---
    @property
    def location(self) -> np.ndarray:
        return self._loc

    @location.setter
    def location(self, arr: Iterable[Number]) -> None:
        a = np.asarray(arr, dtype=np.float64).reshape(3,)
        # store a copy so external arrays don't alias unless you pass a Vec3.location explicitly later
        self._loc = a.copy()

    # --- x, y, z always reflect/self-update location ---
    @property
    def x(self) -> float: return float(self._loc[0])
    @x.setter
    def x(self, v: Number) -> None: self._loc[0] = float(v)

    @property
    def y(self) -> float: return float(self._loc[1])
    @y.setter
    def y(self, v: Number) -> None: self._loc[1] = float(v)

    @property
    def z(self) -> float: return float(self._loc[2])
    @z.setter
    def z(self, v: Number) -> None: self._loc[2] = float(v)

    # --- construction/serialization matching your API ---
    @classmethod
    def load(cls, data: str) -> "Vec3":
        vals = [float(val) for val in data.split(cls.DELIMITER)]
        return cls(np.array(vals, dtype=float))

    def __str__(self) -> str:
        # keep your delimiter behavior
        return f"{self.x}{self.DELIMITER}{self.y}{self.DELIMITER}{self.z}"

    def __repr__(self) -> str:
        return f"Vec3({self.x:.6g}, {self.y:.6g}, {self.z:.6g})"

    # --- helpers for arithmetic ---
    @staticmethod
    def _coerce(other) -> np.ndarray:
        if isinstance(other, Vec3):
            return other.location
        if np.isscalar(other):
            return np.array([other, other, other], dtype=float)
        a = np.asarray(other, dtype=float)
        if a.shape != (3,):
            raise TypeError("Expected coord, scalar, or array-like of length 3")
        return a

    # --- arithmetic (new object) ---
    def __add__(self, other):      return Vec3(self._loc + self._coerce(other))
    def __sub__(self, other):      return Vec3(self._loc - self._coerce(other))
    def __mul__(self, other):      return Vec3(self._loc * self._coerce(other))
    def __truediv__(self, other):  return Vec3(self._loc / self._coerce(other))

    # --- reflected arithmetic ---
    def __radd__(self, other):     return self.__add__(other)
    def __rsub__(self, other):     return Vec3(self._coerce(other) - self._loc)
    def __rmul__(self, other):     return self.__mul__(other)
    def __rtruediv__(self, other): return Vec3(self._coerce(other) / self._loc)

    # --- in-place arithmetic ---
    def __iadd__(self, other):     self._loc += self._coerce(other); return self
    def __isub__(self, other):     self._loc -= self._coerce(other); return self
    def __imul__(self, other):     self._loc *= self._coerce(other); return self
    def __itruediv__(self, other): self._loc /= self._coerce(other); return self

        
    def copy(self):
        return Vec3(self.location)

    