import math
import pygame
from gui.container import Container
from utils.types.colors import RGBA
from gui.types import ItemAlign, ItemAppend, ClickEvent
from typing import Tuple, Dict, Any
from system.input_handler import input_handler

class SliderInput(Container):
    def __init__(
            self, 
            id: str, w: str, h: str, 
            ticks: int, start_tick: int,
            line_color: RGBA = (0, 0, 0, 255), 
            slider_color: RGBA = (152, 61, 187, 255), 
            active_color: RGBA = (255, 255, 255, 255),
            line_thickness = 1,
            outline_thickness = 1,
            end_anchor_radius = 2,
            **kwargs
        ):

        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below, 
            **kwargs
        )

        self.id = id
        self.relative_x_motion = 0

        self.line_color = line_color
        self.slider_color = slider_color
        self.active_color = active_color

        self.line_thickness = line_thickness
        self.outline_thickness = outline_thickness
        self.end_anchor_radius = end_anchor_radius

        self.ticks = ticks
        self.start_tick = start_tick
        self.current_tick = start_tick

        self.is_active = False
        self.hovered = False
        self.slider_canvas = None
        self.slider_img = None
        self.active_slider_img = None

    def bind_parent(self, parent) -> None:
        super().bind_parent(parent)
        self.slider_canvas = self._create_slider_canvas()
        self.slider_img, self.active_slider_img = self._create_sliders()
    
    def _get_slider_surface(self, with_lines: bool = True) -> pygame.Surface:
        w, h = self.get_size()
        slider_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        if with_lines: slider_surface.blit(self.slider_canvas, (0, 0))

        slider = self.active_slider_img if self.is_active or self.hovered else self.slider_img

        x_position = int((w / (self.ticks)) * self.current_tick)
        slider_rect = slider.get_rect(center=(x_position, h // 2))
        slider_surface.blit(slider, slider_rect)
        
        return slider_surface

    def _create_slider_canvas(self):
        w, h = self.get_size()
        slider_canvas = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.line(slider_canvas, self.line_color, (0, h // 2), (w, h // 2), self.line_thickness)
        pygame.draw.circle(slider_canvas, self.line_color, (self.end_anchor_radius, h // 2), self.end_anchor_radius)
        pygame.draw.circle(slider_canvas, self.line_color, (w - self.end_anchor_radius, h // 2), self.end_anchor_radius)
        return slider_canvas

    def _create_sliders(self) -> Tuple[pygame.Surface, pygame.Surface]:
        _, h = self.get_size()
        slider_surface = pygame.Surface((h, h), pygame.SRCALPHA)
        active_slider_surface = pygame.Surface((h, h), pygame.SRCALPHA)
        
        radius = h // 2
        pygame.draw.circle(slider_surface, self.slider_color, (radius, radius), radius)
        pygame.draw.circle(active_slider_surface, self.slider_color, (radius, radius), radius)
        pygame.draw.circle(active_slider_surface, self.active_color, (radius, radius), radius, width=self.outline_thickness)

        return slider_surface, active_slider_surface
    
    def _update_current_tick(self, mx: int) -> None:
        w, _ = self.get_size()
        rel_x = mx - self.x
        new_current_tick = int(round(rel_x / (w / self.ticks)))
        self.current_tick = max(min(self.ticks, new_current_tick), 0)
    
    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        self.background = self._get_slider_surface(with_lines=False)
        is_above = self.mouse_over(mouse_pos)
        self.hovered = is_above
        if self.is_active:
            if input_handler.is_mouse_button_held(1):
                mx, _ = input_handler.get_mouse_pos()
                self._update_current_tick(mx)
            else:
                self.is_active = False
        elif is_above and click_event == ClickEvent.Left:
            self.is_active = True

        state_dict[self.id] = self.current_tick

    def render(self, surface: pygame.Surface) -> None:
        self.slider_canvas = self._create_slider_canvas()
        self.slider_img, self.active_slider_img = self._create_sliders()
        self.background = self._get_slider_surface()
        super().render(surface)