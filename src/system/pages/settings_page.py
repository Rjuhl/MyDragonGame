import pygame
from system.sound import SoundMixer
from system.settings import global_settings
from gui.page import Page
from gui.text import PixelText
from gui.atoms.slider_input import SliderInput
from gui.atoms.keybind_box import KeyBindBox
from gui.buttons.button import Button
from gui.container import Container
from gui.types import ItemAlign, ItemAppend
from gui.utils.callbacks import previous_page_callback
from decorators import register_page


@register_page
class SettingsPage(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)


        self.volume = global_settings.get("volume")
        self.setting_text = PixelText("Settings", 48, (255, 255, 255, 255), bold=True, outline=1)

        # Will need to be updated inside container to reflect slider changes on update
        self.current_volume_text = self._get_volume_text()

        self.volume_slider = SliderInput("volume_slider", "30%", "10", 100, self.volume) # will need to change start tick

        self.volume_container = Container(
            "100%", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children=[
                PixelText("Volume: ", 18, (255, 255, 255, 255), bold=True, varient=1),
                self.volume_slider,
                self.current_volume_text,
            ],
            gap=40,
        )

        self.key_binds_container = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                self._create_key_bind("Fly Up:", "fly_up"),
                self._create_key_bind("Fly Down:", "fly_down"),
            ],
            padding=(0, 20),
            gap=10
        )

        self.buttons_container = Container(
            "100%", "95%",
            ItemAlign.Center, ItemAlign.Last, ItemAppend.Right,
            children=[
                Button("300", "20", "RETURN", 18, previous_page_callback)
            ],
            gap=20
        )

        self.base_container = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                self.setting_text,
                self.volume_container,
                self.key_binds_container
                
            ],
            backgrounds=[

            ], # Will add back ground here later for now just set background manully
        )
        # Remove these 3 lines when background image is added to base_container
        background = pygame.Surface((640, 360))
        background.fill((217, 202, 221, 255))
        self.base_container.background = background

        self.add_container(0, 0, self.base_container)
        self.add_container(0, 0, self.buttons_container)
    
    def _create_key_bind(self, text: str, field: str):
        return Container(
            "100%", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children=[
                Container(
                    "50%", "20",
                    ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
                    children=[
                        PixelText(text, 14, (255, 255, 255, 255), varient=1),
                    ]
                ),
                Container(
                    "50%", "20",
                    ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
                    children=[
                        KeyBindBox("20", "20", 14, field),
                    ]
                )
            ],
        )

    def _get_volume_text(self) -> PixelText:
        return Container(
            "20", "20",
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Below,
            children=[
                PixelText(str(self.volume), 18, (255, 255, 255, 255), varient=1)
            ]
        )
    
    def _update_volume(self):
        volume = self.context.state["volume_slider"] if "volume_slider" in self.context.state else self.volume
        if volume != self.volume:
            self.volume = volume
            self.volume_container.remove_child(self.current_volume_text)
            self.current_volume_text = self._get_volume_text()
            self.volume_container.add_child(self.current_volume_text)
            self.volume_container.reposition_children()

            global_settings.set("volume", self.volume)
            SoundMixer().set_volume(self.volume / 100)

    
    def update(self):
        self._update_volume()
        self.context.state["items_rendered"] = 0
        super().render()