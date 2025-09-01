from utils.coords import Coord

class Tile:
    delimiter = "$"

    def __init__(self, id, location, is_chunk_border=False):
        self.id = id
        self.location = location
        self.is_chunk_border = is_chunk_border
    
    @classmethod
    def load(cls, data):
        id, location, is_chunk_border = data.split(cls.delimiter)
        return Tile(int(id), Coord.load(location), True if str(is_chunk_border) == 't' else False)
    
    def __str__(self):
        return f"{self.id}{self.delimiter}{str(self.location)}{self.delimiter}{ 't' if self.is_chunk_border else 'f'}"

