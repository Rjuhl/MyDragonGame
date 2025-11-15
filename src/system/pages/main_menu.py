import random
import numpy as np
from gui.page import Page
from gui.text import PixelText
from gui.container import Container
from gui.buttons.text_button import TextButton
from gui.utils.callbacks import quit_game_callback
from gui.types import ItemAlign, ItemAppend
from world.tile import Tile
from world.chunk import Chunk
from utils.coords import Coord
from typing import List, Tuple
from system.game_clock import game_clock
from system.entities.entity import Entity
from decorators import register_page
from system.screen import Screen
from constants import CHUNK_SIZE
from enum import Enum

FALL_SPEED = 0.005
TILE_PLACEMENT_SPEED = 10
ENTITY_PLACEMENT_SPEED = 200
CHUNK_MOVE_SPEED = 0.005
DROP_HEIGHT = 10
WAIT_PERIOD = 15_000
DOMAIN = 1000
RANGE = 1000

class MMState(Enum):
    Placement = 0
    Wait = 1
    Move = 2


# Will need to set as default page at somepoint
@register_page#(default=True)
class MainMenu(Page):
    def __init__(self, pageContext):
        super().__init__(pageContext)        
        self.chunk = self._get_new_chunk()
        self.time_to_new_chunk = 0
        self.time_since_last_tile_placement = 0
        self.time_since_last_entity_placement = 0
        
        self.screen = Screen()

        self.tiles: List[Tile] = []
        self.entities: List[Entity] = []
        self.tiles_to_render: List[Tile] = []
        self.entities_to_render: List[Entity] = []

        self.state = MMState.Placement

        self._setup_scene()

        # --------- Page Setup --------- #

        play_game_button = TextButton(
            PixelText("Start Game", 24, (238, 161, 88, 255), outline=1),
            PixelText("Start Game", 26, (238, 161, 88, 255), outline_color=(255, 255, 255, 255), outline=1),
            "180", "20", lambda x: None
        )

        settings_button = TextButton(
            PixelText("Settings", 24, (238, 161, 88, 255), outline=1),
            PixelText("Settings", 26, (238, 161, 88, 255), outline_color=(255, 255, 255, 255), outline=1),
            "180", "20", lambda x: None
        )

        quit_button = TextButton(
            PixelText("Leave Game", 24, (238, 161, 88, 255), outline=1),
            PixelText("Leave Game", 26, (238, 161, 88, 255), outline_color=(255, 255, 255, 255), outline=1),
            "180", "20", quit_game_callback
        )

        menu_buttons = Container(
            "100%", "100%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children= [
                play_game_button,
                settings_button,
                quit_button
            ],
            gap=20
        )

        title = PixelText(
            "My Dragon Game", 76, (238, 18, 66, 255), bold=True, outline=2
        )

        content_container = Container(
            "100%", "90%",
            ItemAlign.Center, ItemAlign.First, ItemAppend.Below,
            children=[
                title,
                menu_buttons
            ]
        )

        base_container = Container(
            "100%", "100%", 
            ItemAlign.Center, ItemAlign.Center, ItemAppend.Right,
            children = [
                content_container
            ]
        )
        self.add_container(0, 0, base_container)



    # Still need to have camera move up at end of cycle
    def update(self):
        dt = game_clock.dt


        self._handle_placement_state(dt)
        self._handle_wait_state(dt)
        self._handle_move_state(dt)
        self._render_items(dt)

        self.render()
        if "next_page" not in self.context.state: self.context.state["next_page"] = self.__class__.__name__
        self.context.state["items_rendered"] = len(self.tiles) + len(self.entities_to_render)

    def _handle_placement_state(self, dt: float):
        if self.state != MMState.Placement: return
        self._place_next_tile(dt)
        self._place_next_entity(dt)
        if len(self.tiles_to_render) == len(self.tiles) and len(self.entities_to_render) == len(self.entities):
            self.state = self._get_next_state(self.state)
    
    def _handle_wait_state(self, dt):
        if self.state != MMState.Wait: return
        if self.time_to_new_chunk > WAIT_PERIOD:
            self.time_to_new_chunk = 0
            self.state = self._get_next_state(self.state)
            return
        self.time_to_new_chunk += dt
    
    def _handle_move_state(self, dt):
        if self.state != MMState.Move: return
        self.screen.anchor.move(Coord.view(1, 1, 0), with_listeners=False)
        if len(self.chunk.get_tiles_in_chunk(*self.screen.get_bounding_box())) == 0:
            self.chunk = self._get_new_chunk()
            self._setup_scene()

            self.time_to_new_chunk = 0
            self.time_since_last_placement = 0
            self.tiles_to_render = []
            self.entities_to_render = []
            self.state = self._get_next_state(self.state)
        self.screen.center_anchor()


    def _render_items(self, dt: float) -> None:
        for tile in sorted(self.tiles_to_render, key=lambda t: (t.location.x, -t.location.y, t.location.z)):
            self.context.renderer.asset_drawer.draw_tile(tile, self.screen.cam_offset, None)
            tile.location.z = max(0, tile.location.z - dt * FALL_SPEED) 
        
        render_objs = []
        for entity in self.entities_to_render:
            entity.location.z = max(0, entity.location.z - dt * FALL_SPEED)
            render_objs.extend(entity.get_render_objs())
            if (shadow := entity.serve_shadow()): render_objs.append(shadow)
        
        render_objs.sort(key= lambda r_obj: r_obj.render_order)
        for render_obj in render_objs:
            self.context.renderer.asset_drawer.draw_sprite(render_obj, self.screen.cam_offset)

        self.context.renderer.asset_drawer.blit_dot(self.chunk.location, self.screen.cam_offset)


    def _place_next_tile(self, dt: float) -> None:
        if len(self.tiles_to_render) == len(self.tiles): return

        if self.time_since_last_tile_placement <= TILE_PLACEMENT_SPEED:
            self.time_since_last_tile_placement += dt
            return 
        
        tiles_to_place = min(self.time_since_last_tile_placement // TILE_PLACEMENT_SPEED, len(self.tiles) - len(self.tiles_to_render))
        for _ in range(tiles_to_place):
            tile = self.tiles[len(self.tiles_to_render)]
            tile.location.z += DROP_HEIGHT
            self.tiles_to_render.append(tile)
        
        self.time_since_last_tile_placement = 0


    def _place_next_entity(self, dt: float) -> None:
        if len(self.tiles_to_render) < len(self.tiles) or len(self.entities_to_render) == len(self.entities): return

        if self.time_since_last_entity_placement <= ENTITY_PLACEMENT_SPEED:
            self.time_since_last_entity_placement += dt
            return 

        self.time_since_last_entity_placement = 0
        entity = self.entities[len(self.entities_to_render)]
        entity.location.z += DROP_HEIGHT
        self.entities_to_render.append(entity)


    def _setup_scene(self):
        anchor = Entity(
            self.chunk.location + Coord.math(31, -31, 0),
            Coord.math(0, 0, 0), -1, Coord.math(0, 0, 0)
        )

        self.screen.anchor = anchor
        self.screen.center_anchor()

        self.tiles = self.chunk.get_tiles_in_chunk(*self.screen.get_bounding_box())
        self.entities = [e for e in self.chunk.entities if self.screen.in_bounding_box(e.location)]
        random.shuffle(self.tiles)

    @staticmethod
    def _get_new_chunk() -> Chunk:
        return Chunk(
            "main_menu",
            Coord.chunk(random.randint(0, DOMAIN), random.randint(0, RANGE)),
            id = -1
        )

    @staticmethod
    def _get_next_state(current_state: MMState):
        return {
            MMState.Placement: MMState.Wait,
            MMState.Wait: MMState.Move,
            MMState.Move: MMState.Placement
        }[current_state]
    
    
