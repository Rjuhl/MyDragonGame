from utils.coords import Coord
from system.entities.base_entity import BaseEntity

class Tile(BaseEntity):
    def __init__(self, id, location, is_chunk_border=False, is_water=False, has_obsticle=False):
        super().__init__(location, Coord.math(1, 1, 0))

        self.id = id
        self.is_chunk_border = is_chunk_border
        self.is_water = is_water
        self.has_obsticle = has_obsticle

        self.update_subscribers = set()
    
    @classmethod
    def load(cls, data):
        return Tile(
            int(data["id"]), 
            Coord.load(data["location"]), 
            data["is_chunk_border"],
            data["is_water"],
            data["has_obsticle"]
        )
    
    def subscribe(self, subscriber):
        self.update_subscribers.add(subscriber)

    def unsubscribe(self, subscriber):
        if subscriber in self.update_subscribers:
            self.update_subscribers.remove(subscriber)

    # Will be used in future if tile changes can occur
    def notify_subscribers(self):
        for subscriber in self.update_subscribers:
            subscriber.tile_update(self)

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

