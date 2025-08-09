import time
import pygame, sys
import constants
from world.utils.coords import Coord
from world.map import Map
from system.renderer import Renderer
from pygame.locals import *

def runGame(logger):
    pygame.init()
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24) 
    pygame.display.set_caption(constants.GAME_NAME)
    screen = pygame.display.set_mode(constants.SCREEN_INIT_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF)
    display = pygame.Surface(constants.DISPLAY_SIZE)

    map = Map(Coord.world(0, 0))
    renderer = Renderer(display, map)


    while True:
        dt = clock.tick() 
        display.fill((0,0,0))
        renderer.draw()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        fps = clock.get_fps()           
        text = font.render(f"FPS: {fps:.1f}", True, (255, 0, 0))
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
        screen.blit(text, (10, 10))
        pygame.display.update()
