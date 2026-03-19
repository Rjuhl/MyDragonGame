import sys
import pygame
from pathlib import Path
from system.settings import global_settings
from constants import SCREEN_INIT_SIZE

def close_app():
    from world.game import GameManager
    from system.input_handler import input_handler
    from system.settings import global_settings

    GameManager().save_game()
    input_handler.save()
    global_settings.save()
    pygame.quit()
    sys.exit()

def setup_file_structure():
    # If function is moved the relative path needs updated
    base_data_dir = Path(__file__).parent.parent.parent
    if not base_data_dir.is_dir():
        base_data_dir.mkdir()
        (base_data_dir / 'games').mkdir()
        (base_data_dir / 'metrics').mkdir()

# def get_screen_type():
#     return pygame.FULLSCREEN | pygame.SCALED  if global_settings.get("fullscreen_on") else pygame.RESIZABLE

# def set_screen_mode(screen_mode):
#     return pygame.display.set_mode(SCREEN_INIT_SIZE, screen_mode | pygame.DOUBLEBUF, vsync=1)