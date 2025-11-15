from gui.text import PixelText
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from typing import Tuple, Dict, Any, Callable

class TextButton(Container):
    def __init__(
            self, 
            text: PixelText, hover_text: PixelText, 
            w: str, h: str, callback: Callable[[Dict[Any, Any]], None]
        ):

        self.text = text
        self.hover_text = hover_text
        self.callback = callback

        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below, 
            children=[text], 
            padding=0, 
            gap=0
        )

        self.text.parent_w, self.text.parent_h = self.w, self.h
        self.hover_text.parent_w, self.hover_text.parent_h = self.w, self.h


    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        isAbove = self.mouse_over(mouse_pos)
        self.children = [self.hover_text] if isAbove else [self.text]
        self.reposition_children()
        if isAbove and click_event == ClickEvent.Left: 
            self.callback(state_dict)