from utils.coords import Coord

class Tile:
    def __init__(self, id, location, is_chunk_border=False):
        self.id = id
        self.location = location
        self.is_chunk_border = is_chunk_border
    
    @classmethod
    def load(cls, data):
        return Tile(int(data["id"]), Coord.load(data["location"]), True if data["is_chunk_border"] == 't' else False)
    
    def jsonify(self):
        return {
            "id": self.id,
            "location": self.location.jsonify(),
            "is_chunk_border": self.is_chunk_border
        }
    
    def __str__(self):
        return f"Id: {self.id} -- Location {str(self.location)} -- Is Chunk Border { 't' if self.is_chunk_border else 'f'}"

