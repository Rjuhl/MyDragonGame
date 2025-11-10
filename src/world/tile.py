from utils.coords import Coord
from system.entities.base_entity import BaseEntity

class Tile(BaseEntity):
    def __init__(self, id, location, is_chunk_border=False, is_water=False, has_obsticle=False):
        super().__init__(location, Coord.math(1, 1, 0))

        self.id = id
        self.is_chunk_border = is_chunk_border
        self.is_water = is_water
        self.has_obsticle = has_obsticle
    
    @classmethod
    def load(cls, data):
        return Tile(
            int(data["id"]), 
            Coord.load(data["location"]), 
            data["is_chunk_border"],
            data["is_water"],
            data["has_obsticle"]
        )
    
    def jsonify(self):
        return {
            "id": self.id,
            "location": self.location.jsonify(),
            "is_chunk_border": self.is_chunk_border,
            "is_water": self.is_water,
            "has_obsticle": self.has_obsticle
        }
    
    def __str__(self):
        return f"Id: {self.id} -- Location {str(self.location)} -- Is Chunk Border { self.is_chunk_border }"

