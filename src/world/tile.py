class Tile:
    def __init__(self, id):
        self.id = id
    
    @classmethod
    def load(cls):
        return Tile(0)
    
    def __str__(self):
        pass

