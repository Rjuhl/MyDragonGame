from gui.text import PixelText
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from typing import Tuple, Dict, Any, List, Optional, Callable
from pathlib import Path
from gui.utils.shapes import draw_rect_surface
from utils.types.colors import RGBA
from system.input_handler import input_handler

class Button(Container):
    def __init__(
        self, 
        w: str, h: str, text: str, font_size: int,
        callback: Callable[[Dict[Any, Any]], None],
        background_color: RGBA = (152, 139, 171, 255),
        outline_color: RGBA = (79, 80, 112, 255),
        hover_background_color: RGBA = (181, 166, 193, 255),
        hover_outline_color: RGBA = (255, 255, 255, 255),
        outline_thickness: int = 1,
        include_mouse_held = False
    ):

        text = PixelText(text, font_size, (79, 80, 112, 255), varient=1)
        self.callback = callback

        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below, 
            children=[text], 
            gap=0
        )

        text.parent_w, text.parent_h = self.w, self.h

        self.background_color = background_color
        self.outline_color = outline_color
        self.hover_background_color = hover_background_color
        self.hover_outline_color = hover_outline_color
        self.outline_thickness = outline_thickness

        self.selected = False
        self.include_mouse_held = include_mouse_held

    def _get_background(self, isHovered: bool):
        w, h = self.get_size()
        if isHovered or self.selected: 
            return draw_rect_surface(self.hover_background_color, self.hover_outline_color, self.outline_thickness, w, h)
        return draw_rect_surface(self.background_color, self.outline_color, self.outline_thickness, w, h)

    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        isAbove = self.mouse_over(mouse_pos)
        self.background = self._get_background(isAbove)
        trigger_mouse_held = (self.include_mouse_held and input_handler.is_mouse_button_held(1))
        if isAbove and (click_event == ClickEvent.Left or trigger_mouse_held): 
            self.callback(state_dict)