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
ALPHA = 0.05  # Learning rate (increased to learn faster from experiences)
GAMMA = 0.99  # Discount factor (high to value future rewards)
EPSILON_START = 1.0 # Exploration rate start
EPSILON_DECAY = 0.9999 # Slower exploration rate decay
EPSILON_MIN = 0.01 # Higher minimum exploration (helps escape local maxima)
Q_TABLE_FILE = 'q_table.pkl' # File to save/load Q-table

# DQN parameters
DQN_LEARNING_RATE = 5e-4  # Increased learning rate for DQN
DQN_BATCH_SIZE = 256  # Larger batch size for better learning
DQN_MEMORY_SIZE = 100000  # Larger replay buffer
DQN_TARGET_UPDATE = 5  # More frequent target network updates
DQN_MODEL_FILE = 'dqn_model.pth'

# Random seed for deterministic environment (None for random behavior)
RANDOM_SEED = 42  # Change this value to get different but reproducible environments

WAIT_TIME = 5 # Frames to wait when Q-agent chooses WAIT action

# Player movement directions (assuming these exist)
# DIRECTION_UP = 0
