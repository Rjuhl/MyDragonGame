from enum import Enum

class EntityTypes(Enum):
    STATIC = 1
    CHARACTER = 2
    PROJECTILE = 3
    NONE = 4

class NPCState(Enum):
    HOME = "Home"
    WANDER = "Wander"
    FIGHT = "Fight"
    FLEE = "Flee"
    IDLE = "Idle"

class FoxExtraStates(Enum):
    STEAL = "Steal"

FoxStates = Enum('FoxStates', {
    **NPCState.__members__,
    **FoxExtraStates.__members__
})