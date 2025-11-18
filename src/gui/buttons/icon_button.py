import pygame
from gui.container import Container
from gui.types import ItemAlign, ItemAppend, ClickEvent
from system.entities.sheet import SpriteSheet
from pathlib import Path
from typing import Callable, Dict, Any, Tuple


class IconSheet(SpriteSheet):
    GUI_FOLDER = Path(__file__).parent.parent.parent / 'assets' / 'gui'

    def __init__(self, name: str):
        icon_img_file = self.GUI_FOLDER / 'icons' / name
        icon_data_file = self.GUI_FOLDER / 'jsons' / f'{name.split(".")[0]}.json'

        if not icon_img_file.is_file() or not icon_data_file.is_file():
            raise TypeError(f"Icon with name = {name} does not exist")

        super().__init__(pygame.image.load(icon_img_file).convert_alpha(), name)
        self._load_data(icon_data_file)


class IconButton(Container):
    ACTIVE = 1
    HOVERED = 2
    UNACTIVE = 3

    def __init__(
            self, 
            w: str, h: str, icon: str,
            is_active: Callable[[Dict[Any, Any]], bool],
            click_callback: Callable[[Dict[Any, Any]], None],
            start_active: bool = True,
            **kwargs
        ):

        super().__init__(
            w, h, 
            ItemAlign.Center, ItemAlign.Center, 
            ItemAppend.Below, 
            **kwargs
        )

        self.icon = icon
        self.active = start_active

        self.is_active = is_active
        self.click_callback = click_callback

        self.icon_sheet = IconButton(self.icon)

        self.hovered = False

    def _set_background(self):
        if self.active:
            self.background = self.icon_sheet.get_sprite(self.HOVERED) if self.hovered else self.icon_sheet.get_sprite(self.ACTIVE)
        else: self.background = self.icon_sheet.get_sprite(self.UNACTIVE)

    def handle_mouse_actions(self, mouse_pos: Tuple[int, int], click_event: ClickEvent, state_dict: Dict[Any, Any]) -> None:
        is_above = self.mouse_over(mouse_pos)
        
        self.hovered = is_above
        self.active = self.is_active(state_dict)

        if is_above and click_event == ClickEvent.Left: 
            self.click_callback(state_dict) 

    def render(self, surface: pygame.Surface) -> None:
        self._set_background()
        super().render(surface)