from pygame.time import Clock
from decorators import singleton

@singleton
class GameClock:
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


game_clock = GameClock()
