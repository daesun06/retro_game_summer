from enum import Enum

class PlayerState(Enum):
    ALIVE = 0
    SPLAT = 1
    SPLASH = 2
    EAGLE = 3

class State(Enum):
    MENU = 1
    MANUAL = 2
    GAME_OVER = 3
    AUTO = 4 
