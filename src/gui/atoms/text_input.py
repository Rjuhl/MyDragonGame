import pygame
from gui.container import Container
from gui.text import PixelText
from gui.types import ItemAlign, ItemAppend, ClickEvent
from utils.types.colors import RGBA
from typing import Optional, Tuple, Dict, Any, Callable
from system.input_handler import input_handler

class TextInput(Container):
    def __init__(
        self, id: str, w: str, h: str, font_size: int, 
        font_color: RGBA = (255, 255, 255, 255), 
        outline_color: Optional[RGBA] = (217, 202, 221, 255), 
        hover_color: Optional[RGBA] = (255, 255, 255, 255), 
        selected_color: Optional[RGBA] = (148, 213, 255), #(119, 162, 246, 255),
        background_color: Optional[RGBA] = (152, 139, 171, 128),
        outline_thickness: int = 1, variant: int = 0, char_limit: int = 40,
        verifier: Callable[[str], bool] = lambda s: True,
        **kwargs
    ):
        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Right,
            **kwargs
        )

        self.id = id

        self.text = ""
        self.char_limit = char_limit
        self.verifier = verifier

        self.font_size = font_size
        self.font_color = font_color
        self.variant = variant

        self.outline_thickness = outline_thickness
        self.outline_color = outline_color
        self.hover_color = hover_color
        self.selected_color = selected_color
        
        self.background_color = background_color

        self.selected = False
        self.mouse_above = False

    def _get_background(self) -> None:
        text = PixelText(self.text, self.font_size, self.font_color, varient=self.variant)
        self.children = [text]
        self.reposition_children()

        w, h = self.get_size()
        text.parent_w, text.parent_h = w, h

        outline_color = self.outline_color
        if self.mouse_above: outline_color = self.hover_color
        if self.selected: outline_color = self.selected_color

        input_area = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.background_color: input_area.fill(self.background_color)
        if self.outline_thickness: pygame.draw.rect(input_area, outline_color, input_area.get_rect(), width=self.outline_thickness)

        self.background = input_area

    def _update_text(self) -> None:
        if not self.selected: return
        if input_handler.was_backspace_pressed(): self.text = self.text[:-1]
        self.text += input_handler.get_text_input() if self.verifier(input_handler.get_text_input()) else ""
        self.text = self.text[:self.char_limit]

    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        state_dict[self.id] = self.text.strip()
        is_above = self.mouse_over(mouse_pos)
        self.mouse_above = is_above
        if click_event == ClickEvent.Left:
            self.selected = is_above

    def render(self, surface: pygame.Surface) -> None:
        self._update_text()
        self._get_background()
        super().render(surface)