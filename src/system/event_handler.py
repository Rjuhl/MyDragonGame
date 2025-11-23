import math
import pygame, sys
from pygame.locals import *
from system.game_clock import game_clock
from constants import TEMP_MOVEMENT_FACTOR
from system.id_generator import id_generator
from system.global_vars import game_globals
from system.input_handler import input_handler
from world.game import game_manager

class EventHandler:
    def __init__(self):
        pass

    def event_tick(self):
        if input_handler.quit_requested: self.close_app()

        if input_handler.was_key_pressed(K_c):
            game_globals.chunk_borders_on = not game_globals.chunk_borders_on
        
        if input_handler.was_key_pressed(K_h):
            game_globals.show_hitboxes_on = not game_globals.show_hitboxes_on
        
        if input_handler.was_key_pressed(K_z):
            game_globals.render_debug = not game_globals.render_debug

    def close_app(self):
        game_manager.save_game()
        id_generator.save()
        input_handler.save()
        pygame.quit()
        sys.exit()
