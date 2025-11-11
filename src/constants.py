import math

# Game system constants
GAME_NAME = "My Game [Change Name Later]"
SCREEN_INIT_SIZE = (1280, 960)
FRAME_CAP = 60
TEMP_MOVEMENT_FACTOR = 6 * 2
DISPLAY_SIZE = (640, 360)
# DISPLAY_SIZE = (960, 540)
# DISPLAY_SIZE = (3440, 1440)
TRACKING_BOX_SCALE = 0.65
GRID_RATIO = [2, 1]

# Map constants
TILE_SIZE = 32
WORLD_HEIGHT = TILE_SIZE * 4
CHUNK_SIZE = 64
PADDING = 3

# Physics system constants
SPATIAL_GRID_PARITION_SIZE = 8
MAX_COLLISION_PASSES = 5

# Player constants
MOVEMENT_MAP = {
    (0, 0): (0, 0),
    (1, 0): (1 / math.sqrt(2), 1 / math.sqrt(2)),
    (-1, 0): (-1 / math.sqrt(2), -1 / math.sqrt(2)),
    (0, 1): (-1 / math.sqrt(2), 1 / math.sqrt(2)),
    (0, -1): (1 / math.sqrt(2), -1 / math.sqrt(2)),
    (1, 1): (0, 1),
    (-1, -1): (0, -1),
    (1, -1): (1, 0),
    (-1, 1): (-1, 0)
}

# World constants
PATH_FINDER_CPT = 1000

# To moved later
SEED = 1