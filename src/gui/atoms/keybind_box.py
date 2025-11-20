import pygame
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.text import PixelText
from gui.utils.shapes import draw_rect_surface
from utils.types.colors import RGBA
from system.input_handler import input_handler
from system.game_clock import game_clock
from typing import Tuple, Dict, Any

PLACE_HOLDER_COUNT = 500
ERROR_TIME = 1000

class KeyBindBox(Container):
    def __init__(
        self, 
        w: str, h: str,
        font_size: int, 
        bind_field: str, 
        current_bind: int,
        font_color: RGBA = (255, 255, 255, 255),
        background_color: RGBA = (125, 120, 154, 255),
        outline_color: RGBA = (66, 72, 97, 255),
        focus_color: RGBA = (255, 255, 255, 255),
        error_color: RGBA = (184, 45, 95, 255),
        outline_thickness = 1,
        **kwargs
    ):
        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below,
            **kwargs
        )

        self.font_size = font_size
        self.font_color = font_color

        self.background_color = background_color
        self.outline_color = outline_color
        self.focus_color = focus_color
        self.error_color = error_color
        self.outline_thickness = outline_thickness

        self.bind_field = bind_field

        self.text = self._create_text(input_handler.key_to_text(current_bind))
        self.placeholder_text = self._create_text("_")
        self.current_placeholder = None
        self.current_placeholder_count = 0

        self.is_active = False
        self.is_hovered = False
        self.error_time = 0


    def _draw_button(self):
        if self.error_time > 0:
            self.background = draw_rect_surface(
                self.background_color,
                self.error_color, 
                self.outline_thickness,
                self.w, self.h, corner_radius=2
            )
            self.error_time = max(0, self.error_time - game_clock.dt)
            return

        if self.is_active or self.is_hovered:
            self.background = draw_rect_surface(
                self.background_color,
                self.focus_color, 
                self.outline_thickness,
                self.w, self.h, corner_radius=2
            )
            return
        
        self.background = draw_rect_surface(
            self.background_color,
            self.outline_color, 
            self.outline_thickness,
            self.w, self.h, corner_radius=2
        )


    def _update_text(self):
        if self.is_active:
            if input_handler.was_any_key_pressed():
                text_input = input_handler.get_text_input()
                if input_handler.was_space_pressed():
                    input_handler.set_action_binding(self.bind_field, [pygame.K_SPACE])
                    self.text = self._create_text(input_handler.key_to_text(pygame.K_SPACE))
                    self.is_active = False
                    self.current_placeholder_count = 0
                elif len(text_input) == 1:
                    input_handler.set_action_binding(self.bind_field, [input_handler.text_to_key(text_input)])
                    self.text = self._create_text(text_input)
                    self.is_active = False
                    self.current_placeholder_count = 0
                elif input_handler.was_control_pressed():
                    input_handler.set_action_binding(self.bind_field, [pygame.K_LCTRL, pygame.K_RCTRL])
                    self.text = self._create_text(input_handler.key_to_text(pygame.K_LCTRL))
                    self.is_active = False
                    self.current_placeholder_count = 0
                elif input_handler.was_shift_pressed():
                    input_handler.set_action_binding(self.bind_field, [pygame.K_LSHIFT, pygame.K_RSHIFT])
                    self.text = self._create_text(input_handler.key_to_text(pygame.K_LSHIFT))
                    self.is_active = False
                    self.current_placeholder_count = 0
                else: self.error_time = ERROR_TIME
            if self.current_placeholder_count > PLACE_HOLDER_COUNT:
                if self.current_placeholder is None: self.current_placeholder = self.placeholder_text
                else: self.current_placeholder = None
                self.current_placeholder_count = -game_clock.dt

            self.current_placeholder_count += game_clock.dt


    def _create_text(self, character: str):
        if character.isalpha(): character = character.upper()
        text = PixelText(
            character,
            self.font_size,
            self.font_color,
            varient=1
        )

        text.parent_w = self.w
        text.parent_h = self.h

        return text
    
    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        is_above = self.mouse_over(mouse_pos)
        self.is_hovered = is_above
        if click_event == ClickEvent.Left:
            self.is_active = is_above

    def render(self, surface: pygame.Surface) -> None:
        self._update_text()
        self._draw_button()

        if self.is_active: 
            self.children = [self.current_placeholder] if self.current_placeholder else []
        else: self.children = [self.text]
        self.reposition_children()

        super().render(surface)