from utils.coords import Coord
from system.entities.base_entity import BaseEntity
from system.entities.sprites.tree import Tree
from collections import defaultdict


class ObsiticleMap:
    OBSITCLE_TYPES = { Tree }
    def __init__(self):
        self._data = defaultdict(set)

    def is_obsticle(self, obj: BaseEntity):
        return obj.__class__ in self.OBSITCLE_TYPES
    
    def add_obsticle(self, location: Coord, size: Coord):
        # Only add points that are withing base chunk or currently loaded chunks
        base_chunk = self._get_chunk_tuple(location)
        for x in range(size.x):
            for y in range(size.y):
                curr_location = location + Coord.world(x, y)
                curr_location_tuple = self._get_chunk_tuple(curr_location)
                if curr_location_tuple == base_chunk or curr_location_tuple in self._data:
                    self._data[curr_location_tuple].add(curr_location)


    def remove_obsticle(self, location: Coord, size: Coord):
        for x in range(size.x):
            for y in range(size.y):
                curr_location = location + Coord.world(x, y)
                curr_location_tuple = self._get_chunk_tuple(curr_location)
                if curr_location_tuple in self._data and curr_location in self._data[curr_location_tuple]:
                    self._data[curr_location_tuple].remove(curr_location)

    def remove_chunk(self, location: Coord):
        del self._data[self._get_chunk_tuple(location)]

    def is_free(self, location: Coord):
        chunk = self._get_chunk_tuple(location)
        return chunk in self._data and location not in self._data[chunk]

    def has_chunk(self, location: Coord):
        return self._get_chunk_tuple(location) in self._data

    def _get_chunk_tuple(self, location: Coord):
        return tuple(location.as_chunk_coord())
    