import sys
import pygame
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


# def get_screen_type():
#     return pygame.FULLSCREEN | pygame.SCALED  if global_settings.get("fullscreen_on") else pygame.RESIZABLE

# def set_screen_mode(screen_mode):
#     return pygame.display.set_mode(SCREEN_INIT_SIZE, screen_mode | pygame.DOUBLEBUF, vsync=1)