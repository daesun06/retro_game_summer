import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
import os
import pickle
from collections import deque, namedtuple

# Import necessary game constants/functions if needed (similar to q_learning.py)
from constants import (
    WIDTH, HEIGHT, DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT,
    GAMMA, EPSILON_START, EPSILON_DECAY, EPSILON_MIN, RANDOM_SEED, DX, DY,
    DQN_LEARNING_RATE, DQN_BATCH_SIZE, DQN_MEMORY_SIZE, DQN_TARGET_UPDATE, DQN_MODEL_FILE
)

# Check if CUDA is available and set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Define the structure for experiences stored in the replay memory
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward', 'done'))

class ReplayMemory:
    """A cyclic buffer of bounded size that holds the transitions observed recently."""
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition."""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class DQN(nn.Module):
    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        # Enhanced network architecture with more layers and neurons
        self.layer1 = nn.Linear(n_observations, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.layer2 = nn.Linear(256, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.layer3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.layer4 = nn.Linear(128, n_actions)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        # Apply batch normalization during training, but not for single sample inference
        if x.size(0) == 1:  # Single sample inference
            x = F.relu(self.layer1(x))
            x = F.relu(self.layer2(x))
            x = F.relu(self.layer3(x))
        else:  # Batch processing during training
            x = F.relu(self.bn1(self.layer1(x)))
            x = self.dropout(x)
            x = F.relu(self.bn2(self.layer2(x)))
            x = self.dropout(x)
            x = F.relu(self.bn3(self.layer3(x)))
        
        return self.layer4(x)

class DQNAgent:
    def __init__(self, actions, state_size, batch_size=DQN_BATCH_SIZE, memory_size=DQN_MEMORY_SIZE, target_update=DQN_TARGET_UPDATE):
        self.actions = actions
        self.n_actions = len(actions)
        self.state_size = state_size # Dimensionality of the state input to the NN
        self.batch_size = batch_size
        self.gamma = GAMMA
        self.epsilon = EPSILON_START
        self.epsilon_decay = EPSILON_DECAY
        self.epsilon_min = EPSILON_MIN
        self.target_update = target_update # How often to update the target network
        self.random = random.Random(RANDOM_SEED)
        self.steps_done = 0
        
        # Create policy and target networks
        self.policy_net = DQN(state_size, self.n_actions).to(device)
        self.target_net = DQN(state_size, self.n_actions).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval() # Target network is only for inference

        # Using the hyperparameters from constants.py
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=DQN_LEARNING_RATE)
        self.memory = ReplayMemory(memory_size)
        
        # Performance tracking (similar to QLearningAgent)
        self.best_score = 0
        self.scores_history = []
        self.avg_score = 0
        self.total_deaths = 0
        self.total_steps = 0
        self.best_epoch = 0
        
        # Training stabilization
        self.loss_history = []
        self.reward_history = []
        self.epsilon_adjustment_frequency = 100  # Check to adjust epsilon every N steps

        # Load model if exists
        self.model_file = DQN_MODEL_FILE
        
        # Define known row types for one-hot encoding
        self.known_row_types = ['Grass', 'Road', 'Rail', 'Water', 'Pavement', 'Dirt', 'None']
        self.row_type_to_index = {name: i for i, name in enumerate(self.known_row_types)}
        self.num_row_types = len(self.known_row_types)
        
        # Verify state_size matches expectation (1+1+1+1+1+1 + 2*num_row_types)
        expected_state_size = 6 + 2 * self.num_row_types
        if state_size != expected_state_size:
             print(f"WARNING: Initialized DQNAgent state_size {state_size} does not match expected {expected_state_size} based on row types.")
             # Adjust internal state_size? Or rely on the provided one?
             # Let's trust the provided state_size for network creation but keep the warning.
             # self.state_size = expected_state_size # Optionally force adjustment

        self.load_model()

    def _one_hot_encode(self, row_type_name):
        """Converts a row type name to a one-hot encoded list."""
        vector = [0.0] * self.num_row_types
        index = self.row_type_to_index.get(row_type_name)
        if index is not None:
            vector[index] = 1.0
        else:
            print(f"Warning: Unknown row type encountered: {row_type_name}")
            # Optionally map unknown types to 'None' or handle differently
            none_index = self.row_type_to_index.get('None')
            if none_index is not None: vector[none_index] = 1.0 
        return vector

    def get_state(self, player, game):
        """
        Calculates a state representation suitable for the DQN using one-hot encoding.
        Returns a PyTorch tensor or None.
        """
        q_state = self._get_q_learning_state_representation(player, game)
        if q_state is None:
            return None
            
        try:
            player_x_bin, current_row_type, next_row_type, on_cooldown, \
                dist_left, dist_right, dist_ahead, dist_behind = q_state
            
            # One-hot encode row types
            current_row_onehot = self._one_hot_encode(current_row_type)
            next_row_onehot = self._one_hot_encode(next_row_type)
            
            # Combine numerical features and one-hot vectors
            state_vector = (
                [float(player_x_bin)] + 
                [float(on_cooldown)] + 
                [float(dist_left)] + 
                [float(dist_right)] + 
                [float(dist_ahead)] + 
                [float(dist_behind)] + 
                current_row_onehot + 
                next_row_onehot
            )
            
            # Ensure the vector length matches self.state_size
            if len(state_vector) != self.state_size:
                 # This warning now suggests a mismatch between calculation and initialization
                 print(f"Critical Warning: Final state vector length ({len(state_vector)}) != initialized state_size ({self.state_size}). Check row types or DQN_STATE_SIZE in main.py.")
                 return None 
                 
            return torch.tensor(state_vector, dtype=torch.float32, device=device).unsqueeze(0)
        except Exception as e:
            print(f"Error processing state {q_state}: {e}")
            return None
            
    def _get_q_learning_state_representation(self, player, game):
        """
        Internal helper to get the discrete state tuple using the same logic as QLearningAgent.
        Copied and adapted from q_learning.py for consistency.
        """
        # --- Constants & Setup ---
        X_BINS = 10  
        VIEW_DISTANCE_X = 80 
        player_x = player.x
        player_y = player.y
        player_width_half = 16 

        # --- Find Relevant Rows ---
        current_row = None
        next_row = None
        prev_row = None
        target_y_up = player_y + DY[DIRECTION_UP] * player.MOVE_DISTANCE
        target_y_down = player_y + DY[DIRECTION_DOWN] * player.MOVE_DISTANCE

        for row in game.rows:
            if row.y == player_y:
                current_row = row
            elif row.y == target_y_up:
                next_row = row
            elif row.y == target_y_down:
                 prev_row = row 
        
        if current_row is None:
            # print("State Error: Current row not found.")
            return None 

        current_row_type = type(current_row).__name__
        next_row_type = type(next_row).__name__ if next_row else 'None'

        # --- Obstacle Proximity Calculation --- 
        DIST_BINS = [35, 60, VIEW_DISTANCE_X]
        DEFAULT_DIST_BIN = len(DIST_BINS)

        def quantize_distance(dist):
            for i, threshold in enumerate(DIST_BINS):
                if dist < threshold:
                    return i
            return DEFAULT_DIST_BIN

        dist_left_bin = DEFAULT_DIST_BIN
        dist_right_bin = DEFAULT_DIST_BIN
        dist_ahead_bin = DEFAULT_DIST_BIN
        dist_behind_bin = DEFAULT_DIST_BIN

        min_dist_left = float('inf')
        min_dist_right = float('inf')
        min_dist_ahead = float('inf')
        min_dist_behind = float('inf')

        if current_row and hasattr(current_row, 'children'):
            for obs in current_row.children:
                obs_x = obs.pos[0]
                relative_x = obs_x - player_x
                dist_x = abs(relative_x)
                if 0 < relative_x < VIEW_DISTANCE_X: min_dist_right = min(min_dist_right, dist_x)
                elif -VIEW_DISTANCE_X < relative_x <= 0: min_dist_left = min(min_dist_left, dist_x)
            dist_left_bin = quantize_distance(min_dist_left)
            dist_right_bin = quantize_distance(min_dist_right)

        if next_row and hasattr(next_row, 'children'):
            landing_x = player_x
            for obs in next_row.children:
                obs_x = obs.pos[0]; relative_x_landing = obs_x - landing_x
                dist_x_landing = abs(relative_x_landing)
                min_dist_ahead = min(min_dist_ahead, dist_x_landing)
            dist_ahead_bin = quantize_distance(min_dist_ahead)

        if prev_row and hasattr(prev_row, 'children'):
             target_x_down = player_x + DX[DIRECTION_DOWN] * player.MOVE_DISTANCE
             for obs in prev_row.children:
                 obs_x = obs.pos[0]; relative_x_behind = obs_x - target_x_down
                 dist_x_behind = abs(relative_x_behind)
                 min_dist_behind = min(min_dist_behind, dist_x_behind)
             dist_behind_bin = quantize_distance(min_dist_behind)

        # --- Discretize State Components --- 
        player_x_bin = min(int(player_x / (WIDTH / X_BINS)), X_BINS - 1)
        on_cooldown = player.jump_cooldown > 0 
                    
        # --- Final State Tuple --- 
        state_tuple = (
            player_x_bin, current_row_type, next_row_type, on_cooldown, 
            dist_left_bin, dist_right_bin, dist_ahead_bin, dist_behind_bin
        )
        return state_tuple

    def choose_action(self, state_tensor):
        """Chooses an action using epsilon-greedy policy based on DQN output."""
        if state_tensor is None: # Handle invalid states
             # print("Choose Action Warning: Received None state tensor. Choosing random action.")
             return self.random.choice(self.actions) # Default random action
             
        sample = self.random.uniform(0, 1)
        eps_threshold = self.epsilon
        self.steps_done += 1
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        # Add noise to exploration to escape local maxima
        if self.steps_done % 500 == 0 and self.avg_score < 30:
            # If we're stuck in low scores, occasionally boost exploration
            eps_threshold = max(eps_threshold, 0.1)
            
        if sample > eps_threshold:
            with torch.no_grad():
                # t.max(1) will return the largest column value of each row.
                # second column on max result is index of where max element was
                # found, so we pick action with the larger expected reward.
                q_values = self.policy_net(state_tensor)
                # print(f"State: {state_tensor.squeeze().tolist()}, Q-Values: {q_values.tolist()}") # Debug
                action_index = q_values.max(1)[1].view(1, 1)
                return self.actions[action_index.item()]
        else:
            # print("Exploring: Choosing random action.") # Debug
            return self.random.choice(self.actions)

    def learn(self):
        """Perform one step of the optimization (on the policy network)."""
        if len(self.memory) < self.batch_size:
            return # Not enough samples in memory yet

        transitions = self.memory.sample(self.batch_size)
        # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for detailed explanation).
        # This converts batch-array of Transitions to Transition of batch-arrays.
        batch = Transition(*zip(*transitions))

        # Filter out None states before creating tensors
        non_final_mask_list = [s is not None for s in batch.next_state]
        non_final_next_states_list = [s for s in batch.next_state if s is not None]

        # Ensure state batch doesn't contain None
        # If a state was None during push, it might cause issues here
        # We assume get_state handles None and pushes valid tensors or skips
        state_list = [s for s in batch.state if s is not None]
        if len(state_list) != self.batch_size:
            # print(f"Warning: Mismatch in state batch size after filtering Nones. Expected {self.batch_size}, got {len(state_list)}. Skipping learn step.")
            # This indicates an issue with how states (especially initial/terminal) are handled
            return 
            
        state_batch = torch.cat(state_list) 
        action_batch = torch.tensor([self.actions.index(a) for a in batch.action], 
                                    dtype=torch.int64, device=device).unsqueeze(1)
        reward_batch = torch.tensor(batch.reward, dtype=torch.float32, device=device).unsqueeze(1)
        done_batch = torch.tensor([float(d) for d in batch.done], dtype=torch.float32, device=device).unsqueeze(1)

        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the columns of actions taken.
        # These are the actions which would've been taken for each batch state according to policy_net
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states.
        next_state_values = torch.zeros(self.batch_size, device=device)
        if len(non_final_next_states_list) > 0:
            non_final_next_states = torch.cat(non_final_next_states_list)
            # Double DQN: Use policy_net to select action, target_net to evaluate it
            with torch.no_grad():
                # Select best actions using policy network
                next_action_indices = self.policy_net(non_final_next_states).max(1)[1].unsqueeze(1)
                # Evaluate those actions using target network
                next_state_action_values = self.target_net(non_final_next_states).gather(1, next_action_indices).squeeze(1)
                non_final_mask = torch.tensor(non_final_mask_list, dtype=torch.bool, device=device)
                next_state_values[non_final_mask] = next_state_action_values
            
        # Compute the expected Q values: reward + gamma * V(s_{t+1}) * (1 - done)
        # We multiply by (1 - done_batch) so that terminal states have a value of 0
        expected_state_action_values = reward_batch + (self.gamma * next_state_values.unsqueeze(1) * (1 - done_batch))

        # Compute Huber loss (or Smooth L1 loss)
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values)
        
        # Track loss for adaptive learning
        self.loss_history.append(loss.item())
        if len(self.loss_history) > 100:
            self.loss_history.pop(0)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # Update target network periodically
        if self.steps_done % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
            
        # Adaptive epsilon adjustment
        if self.steps_done % self.epsilon_adjustment_frequency == 0 and len(self.scores_history) > 10:
            recent_scores = self.scores_history[-10:]
            if max(recent_scores) == self.best_score and self.best_score > 100:
                # If we're not improving but have a good best score, decrease epsilon to exploit more
                self.epsilon = max(self.epsilon_min, self.epsilon * 0.9)
            elif max(recent_scores) < 0.5 * self.best_score:
                # If recent performance is significantly worse than best, increase exploration
                self.epsilon = min(0.2, self.epsilon * 1.1)  # Boost exploration but cap it
            
    def update_stats(self, score, is_death=False):
        # Identical to QLearningAgent.update_stats
        self.scores_history.append(score)
        if len(self.scores_history) > 100: self.scores_history.pop(0)
        if score > self.best_score: 
            self.best_score = score
            from main import epoch_count # Access global epoch count
            self.best_epoch = epoch_count
        if self.scores_history: self.avg_score = sum(self.scores_history) / len(self.scores_history)
        if is_death: self.total_deaths += 1
        self.total_steps += 1 # Note: This counts episodes/deaths, steps_done counts learning steps

    def save_model(self):
        """Saves the policy network state and optimizer state."""
        try:
            state = {
                'policy_net_state_dict': self.policy_net.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'steps_done': self.steps_done,
                'scores_history': self.scores_history,
                'best_score': self.best_score,
                'avg_score': self.avg_score,
                'total_deaths': self.total_deaths,
                'best_epoch': self.best_epoch
            }
            torch.save(state, self.model_file)
            print(f"Saved DQN model and stats to {self.model_file}")
        except Exception as e:
            print(f"Error saving DQN model: {e}")
            
    def load_model(self):
        """Loads the policy network state and optimizer state."""
        if os.path.exists(self.model_file):
            try:
                checkpoint = torch.load(self.model_file, map_location=device)
                self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
                self.target_net.load_state_dict(self.policy_net.state_dict()) # Sync target net
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                self.epsilon = checkpoint.get('epsilon', EPSILON_START) # Load saved epsilon
                self.steps_done = checkpoint.get('steps_done', 0)
                # Load stats
                self.scores_history = checkpoint.get('scores_history', [])
                self.best_score = checkpoint.get('best_score', 0)
                self.avg_score = checkpoint.get('avg_score', 0)
                self.total_deaths = checkpoint.get('total_deaths', 0)
                self.best_epoch = checkpoint.get('best_epoch', 0)
                print(f"Loaded DQN model and stats from {self.model_file}. Epsilon: {self.epsilon:.5f}")
                self.target_net.eval() # Ensure target net is in eval mode
            except Exception as e:
                print(f"Error loading DQN model: {e}. Starting fresh.")
        else:
            print(f"No DQN model file found at {self.model_file}. Initializing new model.")

# Example usage (for testing structure, won't run in game context directly)
if __name__ == '__main__':
    # Define necessary parameters for standalone testing
    dummy_actions = [DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT]
    
    # *** IMPORTANT: Update STATE_FEATURE_COUNT based on the new encoding ***
    # 6 numerical + 2 * 7 one-hot = 20
    STATE_FEATURE_COUNT = 20 
    
    agent = DQNAgent(actions=dummy_actions, state_size=STATE_FEATURE_COUNT)
    
    # --- Mock Game Objects (for testing get_state) ---
    class MockPlayer:
        def __init__(self):
            self.x = WIDTH // 2
            self.y = HEIGHT - 80 # Start near bottom
            self.jump_cooldown = 0
            self.MOVE_DISTANCE = 1 # Need this attribute
            
    class MockRow:
        def __init__(self, y, row_type="Grass"):
            self.y = y
            self.children = []
            # Simulate __name__ for type checking
            self.__class__ = type(row_type, (object,), {"__name__": row_type})
            
    class MockGame:
        def __init__(self):
            self.rows = [MockRow(y=HEIGHT - 40 * i, row_type="Road" if i % 3 == 1 else "Grass") for i in range(1, 6)]
            # Add some mock obstacles
            if hasattr(self.rows[1], 'children'):
                 # Mock actor with pos attribute
                 mock_obstacle = type('MockObstacle', (object,), {'pos': (WIDTH // 2 + 50, self.rows[1].y)})
                 self.rows[1].children.append(mock_obstacle()) 

    mock_player = MockPlayer()
    mock_game = MockGame()
    
    print("Testing DQNAgent initialization and state retrieval...")
    state_tensor = agent.get_state(mock_player, mock_game)
    if state_tensor is not None:
        print(f"Successfully got state tensor: {state_tensor.shape}")
        print(f"State vector: {state_tensor.squeeze().tolist()}")
        action = agent.choose_action(state_tensor)
        print(f"Chosen action: {action}")
        
        # Simulate a transition
        next_state_tensor = agent.get_state(mock_player, mock_game) # Assume state didn't change for simplicity
        reward = 1.0
        done = False
        if state_tensor is not None and next_state_tensor is not None:
            agent.memory.push(state_tensor, action, next_state_tensor, reward, done)
            print(f"Pushed transition to memory. Memory size: {len(agent.memory)}")
            
            # Simulate filling memory and learning
            print("Simulating learning...")
            for _ in range(agent.batch_size + 5):
                 # Push dummy data (replace with realistic transitions)
                 st = agent.get_state(mock_player, mock_game)
                 act = agent.random.choice(agent.actions)
                 nst = agent.get_state(mock_player, mock_game)
                 rew = agent.random.uniform(-1, 1)
                 dn = agent.random.choice([True, False])
                 if st is not None and nst is not None:
                     agent.memory.push(st, act, nst, rew, dn)
                     
            agent.learn() # Try learning step
            print("Learn step executed.")
    else:
        print("Failed to get state tensor.")

    # Test saving/loading
    agent.save_model()
    agent_loaded = DQNAgent(actions=dummy_actions, state_size=STATE_FEATURE_COUNT)
    # Note: Loading happens automatically in __init__ if file exists
    
    print("DQN Agent structure test complete.") 
