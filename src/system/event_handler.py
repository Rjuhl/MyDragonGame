import math
import pygame, sys
from pygame.locals import *
from system.game_clock import game_clock
from constants import TEMP_MOVEMENT_FACTOR

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
                    pygame.quit()
                    sys.exit()
