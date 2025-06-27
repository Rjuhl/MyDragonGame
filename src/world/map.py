import numpy as np

# For now map is very simple it will just return a matrix that is the 'map'

class Map:
    def __init__(self):
        # self.map = np.zeros((50, 50))
        # self.map[0:10, 0:10] = 1
        # self.map[20:30, 20:30] = 1
        self.map = np.ones((40, 40))
    def getMap(self):
        return self.map