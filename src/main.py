import pygame
import constants
from utils.coords import Coord
from world.map import Map
from system.renderer import Renderer
from system.event_handler import EventHandler
from system.game_clock import game_clock
from pygame.locals import *

def runGame(logger):
    pygame.init()
    font = pygame.font.Font(None, 24) 
    pygame.display.set_caption(constants.GAME_NAME)
    screen = pygame.display.set_mode(constants.SCREEN_INIT_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF , vsync=1)
    display = pygame.Surface(constants.DISPLAY_SIZE)

    map = Map(Coord.world(0, 0))
    renderer = Renderer(display, map)
    event_handler = EventHandler()

    while True:
        game_clock.tick() 
        display.fill((0,0,0))

        renderer.update()
        items_rendered = renderer.draw()

        event_handler.event_tick()

        fps = game_clock.fps           
        fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 0, 0))
        tiles_text = font.render(f"Tiles Rendered: {items_rendered}", True, (255, 0, 0))
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
        screen.blit(fps_text, (10, 10))
        screen.blit(tiles_text, (10, 26))
        pygame.display.flip()
