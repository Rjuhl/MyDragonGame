from utils.coords import Coord

class BaseEntity:
    def __init__(self, location: Coord, size: Coord):
        self.location = location
        self.size = size