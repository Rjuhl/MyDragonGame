import sys
import pygame

def close_app():
    from world.game import GameManager
    from system.input_handler import input_handler
    from system.settings import global_settings

    GameManager().save_game()
    input_handler.save()
    global_settings.save()
    pygame.quit()
    sys.exit()