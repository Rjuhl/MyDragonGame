from gui.text import PixelText
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from typing import Tuple, Dict, Any, List, Optional, Callable
from pathlib import Path

class BasicButton(Container):
    def __init__(self, w: str, h: str, text: str, font_size: int, callback: Callable[[Dict[Any, Any]], None]):
        current_dir = Path(__file__).parent
        asset_dir = current_dir.parent.parent.parent / 'assets' / 'gui' / 'backgrounds'

        backgrounds = [asset_dir / 'basic_button.png', asset_dir / 'basic_button_hovered.png']
        text = PixelText(text, font_size, (79, 80, 112, 255))

        self.callback = callback


        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below, 
            children=[text], 
            backgrounds=backgrounds, 
            padding=0, 
            gap=0
        )

        text.parent_w, text.parent_h = self.w, self.h

    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        isAbove = self.mouse_over(mouse_pos)
        self.background = self.backgrounds[1] if isAbove else self.backgrounds[0]
        if isAbove and click_event == ClickEvent.Left: 
            self.callback(state_dict)