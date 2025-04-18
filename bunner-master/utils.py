import sys
import pgzero
import pygame
import random
import numpy as np
from constants import RANDOM_SEED

# Key status tracking for input handling
key_status = {}

def key_just_pressed(key):
    """Check if a key was just pressed this frame."""
    global key_status
    result = False
    prev_status = key_status.get(key, False)
    if not prev_status and pygame.key.get_pressed()[key]:
        result = True
    key_status[key] = pygame.key.get_pressed()[key]
    return result

def display_number(screen, n, colour, x, align):
    """Display a number on the screen."""
    n = str(n)  
    for i in range(len(n)):
        screen.blit("digit" + str(colour) + n[i], (x + (i - len(n) * align) * 25, 0))

def check_python_version():
    """Check if the Python version is compatible."""
    major, minor = sys.version_info[0:2]
    if major < 3 or (major == 3 and minor < 5):
        sys.exit('This game requires Python 3.5 or higher.')

def init_random_seeds(seed=None):
    """
    Initialize random seeds for all random number generators to make the environment deterministic.
    
    Args:
        seed: The random seed to use. If None, no seeding is done (random behavior).
    
    Returns:
        The seed that was used (useful if you want to log it)
    """
    if seed is not None:
        # Seed Python's random module
        random.seed(seed)
        
        # Seed NumPy's random module if available (used by some learning algorithms)
        try:
            np.random.seed(seed)
        except ImportError:
            pass
        
        print(f"Random seed initialized to: {seed}")
    else:
        print("Random seed not set - environment will be non-deterministic")
    
    return seed 
