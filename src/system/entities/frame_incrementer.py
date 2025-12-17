from system.game_clock import game_clock
from typing import Callable


class FrameIncrementer:
    def __init__(self, start: float, times_step: float, incrementer: Callable[[float], float]):
        self.start = start
        self.current = start
        
        self.time_step = times_step
        self.current_time = 0 

        self.incrementer = incrementer

    def reset(self):
        self.current = self.start
        self.current = 0
    
    def tick(self):
        if self._update_clock():
            self.current = self.incrementer(self.current)
        return self.current

    def _update_clock(self):
        self.current_time += game_clock.dt
        if self.current_time >= self.time_step:
            self.current_time -= self.time_step
            return True
        return False