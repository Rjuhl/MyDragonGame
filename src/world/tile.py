from utils.coords import Coord

class Tile:
    delimiter = "$"

    def __init__(self, id, location):
        self.id = id
        self.location = location
    
    @classmethod
    def load(cls, data):
        id, location = data.split(cls.delimiter)
        return Tile(int(id), Coord.load(location))
    
    def __str__(self):
        return f"{self.id}{self.delimiter}{str(self.location)}"

