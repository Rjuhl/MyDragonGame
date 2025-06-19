import pygame
import constants
from system.map import Map
from system.renderer import Renderer

def runGame(logger):
    pygame.init()
    pygame.display.set_caption(constants.GAME_NAME)
    screen = pygame.display.set_mode(constants.SCREEN_INIT_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF)
    display = pygame.Surface(constants.DISPLAY_SIZE)

    renderer = Renderer(display)
    

    