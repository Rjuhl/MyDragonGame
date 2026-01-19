from system.game_clock import game_clock

class Cooldown:
    def __init__(self, cooldown: int):
        self.cooldown = cooldown
        self.time_passed = 0
    
    def tick(self):
        self.time_passed += game_clock.dt
    
    def ready(self, reset=True):
        ready = self.time_passed >= self.cooldown
        if ready and reset: self.reset() 
        return ready
    
    def reset(self):
        self.time_passed = 0