import math
import pygame, sys
from pygame.locals import *
from system.game_clock import game_clock
from constants import TEMP_MOVEMENT_FACTOR
from system.id_generator import id_generator
from system.global_vars import game_globals

class EventHandler:
    def __init__(self):
        pass

    def event_tick(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.close_app()

                # Turn on chunk borders 
                if event.key == K_c:
                    game_globals.chunk_borders_on = not game_globals.chunk_borders_on

    def close_app(self):
        id_generator.save()
        pygame.quit()
        sys.exit()