import math

# Game system constants
GAME_NAME = "My Dragon Game"
SCREEN_INIT_SIZE = (1280, 960)
SCREEN_INIT_SIZE = (1280 / 2, 960 / 2)
FRAME_CAP = 60
TEMP_MOVEMENT_FACTOR = 6 #* 4
DISPLAY_SIZE = (640, 360) # Final game divide this by 1.5?
# DISPLAY_SIZE = (960, 540)
#DISPLAY_SIZE = (3440, 1440)
#DISPLAY_SIZE = (3440 * 2, 1440 * 2)
TRACKING_BOX_SCALE = 0.65
GRID_RATIO = [2, 1]
BANNER_SIZE = (384, 32)
DEFAULT_BUTTON_COOLDOWN = 100

# Map constants
TILE_SIZE = 32
WORLD_HEIGHT = TILE_SIZE * 4
CHUNK_SIZE = 64
ASSET_SIZE = 8
PADDING = 3
TILE_GROUP_DRAW_SIZE = 8 # 16
TILE_ASSET_SHOWN_SIZE = (32, 16)

assert CHUNK_SIZE % TILE_GROUP_DRAW_SIZE == 0

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
PATH_FINDER_CPT = 64

# To moved later
SEED = 1

# Spawn Weights
BLANK_WEIGHT = 100_000
FOX_BURROW_WIEGHT = 15
OUTPOST_WEIGHT = 8 * 3

# Sound Constants
MAX_SOUND_DISTANCE = 40
DEFAULT_SOUND_VOLUME = 80

# NPC contants
WIZARD_AGGRESSION_RANGE = 24

IS_TILE_GROUPING_ON = True
DEGUB_ON = True