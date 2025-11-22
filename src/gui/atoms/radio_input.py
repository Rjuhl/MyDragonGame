import pygame
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from gui.buttons.button import Button
from utils.types.colors import RGBA
from typing import List, Optional
from typing import Tuple, Dict, Any, List, Optional, Callable

class RadioInput(Container):
    def __init__(
        self,
        id: str, w: str, h: str, 
        font_size: int,
        options: List[str],
        default_selection: int,
        background_color: RGBA = (152, 139, 171, 255),
        outline_color: RGBA = (79, 80, 112, 255),
        hover_background_color: RGBA = (181, 166, 193, 255),
        hover_outline_color: RGBA = (255, 255, 255, 255),
        outline_thickness: int = 1,
        **kwargs
    ):
        self.id = id
        self.options = options

        self.index_hovered = None
        self.index_selected = default_selection

        self.background_color = background_color
        self.outline_color = outline_color
        self.hover_background_color = hover_background_color
        self.hover_outline_color = hover_outline_color
        self.outline_thickness = outline_thickness

        self.font_size = font_size

        super().__init__(
            w, h, 
            ItemAlign.First, ItemAlign.Center, 
            ItemAppend.Right,
            **kwargs
        )
    
    def bind_parent(self, parent):
        super().bind_parent(parent)
        w, h = self.get_size()
        item_width = int(round(w / len(self.options)))
        self.children = [
            Button(
                str(item_width), str(h), text, self.font_size, self._create_callback(i), 
                background_color=self.background_color,
                outline_color=self.outline_color,
                hover_background_color=self.hover_background_color,
                hover_outline_color=self.hover_outline_color,
                outline_thickness=self.outline_thickness
            ) for i, text in enumerate(self.options)
        ]
    
    
    def _create_callback(self, index: int) -> Callable[[Dict[Any, Any]], None]:
        def callback(state_dict):
            state_dict[self.id] = index
            self.index_selected = index
        return callback

    def render(self, surface: pygame.Surface) -> None:
        for i, child in enumerate(self.children):
            child.selected = i == self.index_selected
        super().render(surface)