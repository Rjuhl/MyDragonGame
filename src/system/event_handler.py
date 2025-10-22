import math
import pygame, sys
from pygame.locals import *
from system.game_clock import game_clock
from constants import TEMP_MOVEMENT_FACTOR
from system.id_generator import id_generator
from system.global_vars import game_globals
import time

class EventHandler:
    def __init__(self):
        pass

    def event_tick(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.close_app()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return "escape"

                # Turn on chunk borders 
                if event.key == K_c:
                    game_globals.chunk_borders_on = not game_globals.chunk_borders_on

                # Turn on hitboxes
                if event.key == K_h:
                    game_globals.show_hitboxes_on = not game_globals.show_hitboxes_on
                
                if event.key == K_z:
                    game_globals.render_debug = not game_globals.render_debug

    def close_app(self):
        id_generator.save()
        pygame.quit()
        sys.exit()
