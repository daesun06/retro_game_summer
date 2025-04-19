WIDTH = 480 
HEIGHT = 800
TITLE = "Bunner Game"

ROW_HEIGHT = 40
DEBUG_SHOW_ROW_BOUNDARIES = False

# Direction constants
DIRECTION_UP = 0
DIRECTION_RIGHT = 1
DIRECTION_DOWN = 2
DIRECTION_LEFT = 3
DIRECTION_WAIT = 4

# X and Y directions indexed into by in_edge and out_edge in Segment
# The indices correspond to the direction numbers above, i.e. 0 = up, 1 = right, 2 = down, 3 = left
DX = [0, 4, 0, -4, 0]
DY = [-4, 0, 4, 0, 0] 

# Q-learning parameters
ALPHA = 0.01  # Learning rate (Restored for peak performance run)
GAMMA = 0.99  # Discount factor (increased slightly more to value future survival)
EPSILON_START = 1.0 # Exploration rate start
EPSILON_DECAY = 0.99995 # Slower exploration rate decay
EPSILON_MIN = 0.001 # Minimum exploration rate (Restored for peak performance run)
Q_TABLE_FILE = 'q_table.pkl' # File to save/load Q-table

# Random seed for deterministic environment (None for random behavior)
RANDOM_SEED = 42  # Change this value to get different but reproducible environments

WAIT_TIME = 5 # Frames to wait when Q-agent chooses WAIT action

# Player movement directions (assuming these exist)
# DIRECTION_UP = 0
