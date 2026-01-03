import json
import pygame
from utils.coords import Coord
from decorators import singleton
from constants import MOVEMENT_MAP
from typing import Dict, List, Optional
from pathlib import Path
from system.event_handler import EventHandler


@singleton
class InputHandler:
    """
        Centralized per-frame input manager.

        Consumes the pygame event queue once per frame and exposes:
        - edge-triggered input (pressed/released this frame)
        - continuous input (keys/buttons currently held)

        Tracks keyboard, mouse, scroll, text input, and quit events.
        Supports action-to-key mappings so gameplay code can query actions
        instead of raw keycodes.

        Optionally scales mouse coordinates when bound to a screen/display pair.
        Keybindings are persisted to disk as JSON.
    """

    PATH = Path(__file__).parent.parent.parent / 'data' / 'keybinds'

    def __init__(self):
        # -------- Raw input state --------
        # Keyboard
        self.keys_down = set()
        self.keys_up = set()
        self._pressed = None

        # Mouse
        self.mouse_pos = (0, 0)
        self.mouse_rel = (0, 0)
        self.mouse_buttons_held = set()
        self.mouse_buttons_down = set()
        self.mouse_buttons_up = set()
        self.scroll_y = 0

        self.screen = None
        self.display = None

        # Text
        self.text_input = ""

        # Other
        self.quit_requested = False

        # -------- Action mapping (high-level) --------
        # action_name -> list of pygame key constants
        self.action_bindings = {}
        self._load_config()
        

    # -------------------------------------------------------------------------
    # Core update
    # -------------------------------------------------------------------------
    def update(self):
        """
        Call once per frame/tick.
        Consumes the pygame event queue and updates all input state.
        """
        # Clear per-frame state (edge-triggered stuff)
        self.keys_down.clear()
        self.keys_up.clear()
        self.mouse_buttons_down.clear()
        self.mouse_buttons_up.clear()
        self.text_input = ""
        self.scroll_y = 0
        self.quit_requested = False

        # --- 1) Handle discrete events (edges) ---
        for event in EventHandler().events():
            if event.type == pygame.QUIT:
                self.quit_requested = True

            # Keyboard
            elif event.type == pygame.KEYDOWN:
                self.keys_down.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys_up.add(event.key)

            # Text input (for UI / text fields)
            elif event.type == pygame.TEXTINPUT:
                self.text_input += event.text

            # Mouse buttons
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons_down.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_buttons_up.add(event.button)

            # Scroll wheel
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_y += event.y

        # --- 2) Continuous state queries (held state) ---
        # Keyboard "held" state: use key constants as indices
        self._pressed = pygame.key.get_pressed()

        # Mouse continuous data
        buttons = pygame.mouse.get_pressed(num_buttons=5)
        self.mouse_buttons_held = {i + 1 for i, down in enumerate(buttons) if down}
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_rel = pygame.mouse.get_rel()

        if self.screen and self.display:
            sw, sh = self.screen.get_size()
            dw, dh = self.display.get_size()

            # Scale mouse_pos
            raw_x, raw_y = self.mouse_pos
            disp_x = raw_x * dw / sw
            disp_y = raw_y * dh / sh
            self.mouse_pos = (int(disp_x), int(disp_y))

            # Scale mouse_rel
            rel_x, rel_y = self.mouse_rel
            scaled_rel_x = rel_x * dw / sw
            scaled_rel_y = rel_y * dh / sh
            self.mouse_rel = (scaled_rel_x, scaled_rel_y)

    # -------------------------------------------------------------------------
    # Low-level convenience methods (keyboard)
    # -------------------------------------------------------------------------

    def is_key_held(self, key) -> bool:
        """True as long as the key is held down."""
        return bool(self._pressed and self._pressed[key])

    def was_key_pressed(self, key) -> bool:
        """True only on the frame the key was pressed."""
        return key in self.keys_down

    def was_key_released(self, key) -> bool:
        """True only on the frame the key was released."""
        return key in self.keys_up

    # -------------------------------------------------------------------------
    # Low-level convenience methods (mouse)
    # -------------------------------------------------------------------------

    def get_mouse_pos(self):
        self._check_binding()
        return self.mouse_pos

    def get_mouse_rel(self):
        return self.mouse_rel

    def is_mouse_button_held(self, button) -> bool:
        return button in self.mouse_buttons_held

    def was_mouse_button_pressed(self, button) -> bool:
        return button in self.mouse_buttons_down

    def was_mouse_button_released(self, button) -> bool:
        return button in self.mouse_buttons_up

    def get_scroll_y(self):
        return self.scroll_y
    
    def _check_binding(self):
        if self.screen is None or self.display is None:
            raise TypeError(
                "Must bind handler to screen + display before using mouse pos"
            )

    # -------------------------------------------------------------------------
    # Text input
    # -------------------------------------------------------------------------

    def get_text_input(self) -> str:
        """All text characters typed this frame (for UI text fields)."""
        return self.text_input
    
    def was_backspace_pressed(self) -> bool:
        """True only on the frame Backspace was pressed."""
        return pygame.K_BACKSPACE in self.keys_down
    
    def was_space_pressed(self) -> bool:
        """True on the frame the spacebar was pressed."""
        return pygame.K_SPACE in self.keys_down

    def was_control_pressed(self) -> bool:
        """True on the frame either LCTRL or RCTRL was pressed."""
        return (pygame.K_LCTRL in self.keys_down or
                pygame.K_RCTRL in self.keys_down)
    
    def was_shift_pressed(self) -> bool:
        """True on the frame either LSHIFT or RSHIFT was pressed."""
        return (pygame.K_LSHIFT in self.keys_down or
                pygame.K_RSHIFT in self.keys_down)
    
    def was_any_key_pressed(self) -> bool:
        """
        True if any keyboard key was pressed this frame.
        Includes all non-alphanumeric keys.
        """
        return len(self.keys_down) > 0
    

    def text_to_key(self, char: str) -> Optional[int]:
        """Converts a character from TEXTINPUT into pygame int keycodes."""

        if len(char) != 1: return
        try:
            return pygame.key.key_code(char)
        except ValueError:
            pass

    def key_to_text(self, keycode: int) -> str:
        """Converts keycodes to a string"""
        name = pygame.key.name(keycode)
        if len(name) == 1 and name.isalnum():
            return name
        if name == "space": return "SP"
        if name == "left shift": return "LS"
        if name == "right shift": return "RS"
        if name == "left ctrl": return "LC"
        if name == "right ctrl": return "RC"
        return ""


    # -------------------------------------------------------------------------
    # Action mapping
    # -------------------------------------------------------------------------

    def _set_default_bindings(self):
        """
        Set up default action bindings.
        You can tweak/remove these or add your own.
        """
        self.action_bindings = {
            "move_left": [pygame.K_LEFT, pygame.K_a],
            "move_right": [pygame.K_RIGHT, pygame.K_d],
            "move_up": [pygame.K_UP, pygame.K_w],
            "move_down": [pygame.K_DOWN, pygame.K_s],
            "fly_up": [pygame.K_SPACE],
            "fly_down": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "pause": [pygame.K_ESCAPE],
        }

    # -------- Action queries --------
    def is_action_active(self, action: str) -> bool:
        """
        True as long as *any* bound key for this action is held.
        Good for continuous actions like movement.
        """
        if not self._pressed:
            return False
        keys = self.action_bindings.get(action, [])
        return any(self._pressed[k] for k in keys)

    def was_action_pressed(self, action: str) -> bool:
        """
        True only on the frame when any bound key was just pressed.
        Good for one-shot actions like jump, shoot, confirm, pause.
        """
        keys = self.action_bindings.get(action, [])
        return any(k in self.keys_down for k in keys)

    def was_action_released(self, action: str) -> bool:
        """True on the frame when any bound key was released."""
        keys = self.action_bindings.get(action, [])
        return any(k in self.keys_up for k in keys)

    # -------- Remapping helpers --------
    def set_action_binding(self, action: str, keys):
        """
        Replace the key list for an action.
        `keys` can be a single key or an iterable of keys.
        """
        if isinstance(keys, int):
            keys = [keys]
        self.action_bindings[action] = list(keys)

    def add_key_to_action(self, action: str, key: int):
        """
        Add an extra key to an action (e.g., bind both SPACE and Z to 'jump').
        """
        self.action_bindings.setdefault(action, [])
        if key not in self.action_bindings[action]:
            self.action_bindings[action].append(key)

    def remove_key_from_action(self, action: str, key: int):
        """
        Remove a specific key from an action.
        Does nothing if the key isn't bound.
        """
        if action in self.action_bindings and key in self.action_bindings[action]:
            self.action_bindings[action].remove(key)

    # -------- Advanced Queries --------
    def get_player_movement(self) -> Coord:
        """
        Returns a Coord representing movement for this frame based on actions.
        Uses MOVEMENT_MAP to normalize dx, dy, and uses fly_up/down for dz.
        """
        right_active = self.is_action_active("move_right")
        left_active = self.is_action_active("move_left")
        up_active = self.is_action_active("move_up")
        down_active = self.is_action_active("move_down")
        fly_up_active = self.is_action_active("fly_up")
        fly_down_active = self.is_action_active("fly_down")

        dx = int(right_active) - int(left_active)
        dy = int(up_active) - int(down_active)
        dz = int(fly_up_active) - int(fly_down_active)

        dx, dy = MOVEMENT_MAP[(dx, dy)]

        return Coord.math(dx, dy, dz)

    # -------- Loading and Saving ---------
    def save(self) -> None:
        """ Save player configs to a file """
        self.PATH.write_text(json.dumps(self.action_bindings, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def _load_config(self) -> Dict[str, List[int]]:
        """ Load player keybinds later """
        if self.PATH.is_file():
            with self.PATH.open("r", encoding="utf-8") as f:
                self.action_bindings =  json.load(f)
        else: self._set_default_bindings()

    def bind_displays(self, screen: pygame.Surface, dispay: pygame.Surface) -> None:
        """ Bind screen and display so that we can translate mouse pos correctly """
        self.screen = screen
        self.display = dispay
        w, h = self.screen.get_size()
        pygame.mouse.set_pos((w // 2, h // 2))

input_handler = InputHandler()
