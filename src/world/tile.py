class Tile:
    def __init__(self, id, location):
        self.id = id
        self.location = location
    
    @classmethod
    def load(cls):
        return Tile(0)
    
    def __str__(self):
        pass

