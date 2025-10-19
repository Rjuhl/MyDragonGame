import pygame
from gui.container import Container

class Page:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.containers = []

    def add_container(self, x: str, y: str, container: Container) -> None:
        surface_x, surface_y = self.surface.get_size()
        container.parent_w, container.parent_h = surface_x, surface_y
        container_w, container_h = container.get_size()

        if x[-1] == "%":
            pass
        else:
            pass

        if y[-1] == "%":
            pass
        else:
            pass

        self.containers.append(container)


    def render(self):
        for container in self.containers: 
            container.reposition_children()
            container.render(self.surface)

