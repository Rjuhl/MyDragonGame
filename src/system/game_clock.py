import math
from pygame.time import Clock

from constants import FRAME_CAP
from decorators import singleton

@singleton
class GameClock:
    """
        Centralized game timing utility.

        This class wraps `pygame.time.Clock` and provides:
        - a per-frame delta time (`dt`) in milliseconds
        - a smoothed frames-per-second estimate (`fps`)
        - optional frame-rate limiting via `frame_cap`

        It is implemented as a singleton so all systems (movement, animation,
        physics, audio, etc.) reference the same timing source.

        Usage:
            game_clock.tick()   # call once per frame
            dt = game_clock.dt  # milliseconds since last frame
            fps = game_clock.fps
    """

    def __init__(self, frame_cap=None):
        self.clock = Clock()
        self.frame_cap = frame_cap
        self._dt = 0 

    def tick(self):
        self._dt = (
            self.clock.tick()
            if self.frame_cap is None
            else self.clock.tick(self.frame_cap)
        )

    @property
    def dt(self):
        return self._dt

    @property
    def fps(self):
        return self.clock.get_fps()

    @staticmethod
    def _round(number, places=3):
        return math.floor(number * (10 ** places)) / (10 ** places)


game_clock = GameClock(frame_cap=FRAME_CAP)
