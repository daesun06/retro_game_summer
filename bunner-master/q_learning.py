import random
import pickle
import os
from collections import defaultdict

# Import game constants and state/row types (assuming they are needed for state representation)
# Need to be careful about circular imports if q_learning imports from game/player
# It might be better to pass necessary game info (constants, row types) to the agent
from constants import (WIDTH, DX, DY, DIRECTION_UP, DIRECTION_RIGHT, 
                       DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT,
                       ALPHA, GAMMA, EPSILON_START, EPSILON_DECAY, EPSILON_MIN,
                       Q_TABLE_FILE, RANDOM_SEED)
# from player import Bunner # Avoid direct import if possible
# from rows import Grass, Road, Rail, Pavement, Dirt # Avoid direct import if possible
# from game import game # Avoid direct import


class QLearningAgent:
    def __init__(self, actions, batch_size=32):
        self.actions = actions
        self.alpha = ALPHA
        self.gamma = GAMMA
        self.epsilon = EPSILON_START
        self.epsilon_decay = EPSILON_DECAY
        self.epsilon_min = EPSILON_MIN
        
        # Use defaultdict for convenient Q-table initialization
        self.q_table = self.load_q_table()
        
        # Track state visits for optimistic learning rates
        self.state_visits = {}
        
        # Set a deterministic random seed for reproducible learning
        self.random = random.Random(RANDOM_SEED)
        print(f"QLearningAgent initialized with random seed: {RANDOM_SEED}")
        
        # Performance tracking metrics
        self.best_score = 0
        self.scores_history = []
        self.avg_score = 0
        self.total_deaths = 0
        self.total_steps = 0
        self.best_epoch = 0
        
        # Enhanced learning
        self.experience_buffer = []  # For potential experience replay
        self.max_buffer_size = 10000
        self.batch_size = batch_size # Store batch size

    def load_q_table(self):
        if os.path.exists(Q_TABLE_FILE):
            try:
                with open(Q_TABLE_FILE, 'rb') as f:
                    # Load the saved data (expecting a dictionary)
                    saved_data = pickle.load(f)
                    
                    # Check if it's the new format (dictionary) or old format (just q_table)
                    if isinstance(saved_data, dict) and 'q_table' in saved_data and 'epsilon' in saved_data:
                        q_table = saved_data['q_table']
                        loaded_epsilon = saved_data['epsilon']
                        print(f"Loaded Q-table with {len(q_table)} states and Epsilon: {loaded_epsilon:.5f}")
                        # Update the agent's epsilon with the loaded value
                        self.epsilon = loaded_epsilon 
                    else:
                        # Handle old format (just the Q-table) for backward compatibility
                        q_table = saved_data 
                        print(f"Loaded Q-table (old format) with {len(q_table)} states. Epsilon reset to START.")
                        # Epsilon will remain at EPSILON_START as initialized
                        
                    # Ensure it's a defaultdict for compatibility
                    return defaultdict(lambda: {action: 0.0 for action in self.actions}, q_table)
            except Exception as e:
                print(f"Error loading Q-table: {e}. Starting fresh.")
        print("No Q-table found or error loading. Initializing new Q-table.")
        # Initialize Q-table: state -> {action: value} mapping
        # defaultdict returns a default value (a dict of actions with 0.0 value) for unseen states
        return defaultdict(lambda: {action: 0.0 for action in self.actions})

    def save_q_table(self):
        try:
            with open(Q_TABLE_FILE, 'wb') as f:
                # Create a dictionary containing both the Q-table and the current epsilon
                data_to_save = {
                    'q_table': dict(self.q_table), # Convert defaultdict to dict for saving
                    'epsilon': self.epsilon
                }
                pickle.dump(data_to_save, f) 
                print(f"Saved Q-table with {len(self.q_table)} states and Epsilon: {self.epsilon:.5f}")
        except Exception as e:
            print(f"Error saving Q-table: {e}")
            
    def update_stats(self, score, is_death=False):
        """
        Update agent statistics after an episode ends
        Args:
            score: The final score achieved
            is_death: Whether the episode ended with death
        """
        self.scores_history.append(score)
        if len(self.scores_history) > 100:  # Keep last 100 scores
            self.scores_history.pop(0)
            
        if score > self.best_score:
            self.best_score = score
            # Store the current epoch if available
            from main import epoch_count
            self.best_epoch = epoch_count
            
        # Calculate rolling average
        if self.scores_history:
            self.avg_score = sum(self.scores_history) / len(self.scores_history)
            
        if is_death:
            self.total_deaths += 1
            
        self.total_steps += 1
        
        # Adaptive epsilon decay based on performance
        if len(self.scores_history) >= 10:
            recent_avg = sum(self.scores_history[-10:]) / 10
            if recent_avg > self.avg_score:
                # If improving, reduce exploration slightly faster
                self.epsilon = max(self.epsilon_min, self.epsilon * 0.999)

    def get_state(self, player, game):
        """
        Calculates a discrete state representation using quantized distances to nearest obstacles.
        Args:
            player: The Bunner instance.
            game: The Game instance.
        Returns:
            A tuple representing the discrete state, or None if state is invalid.
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
            return None 

        current_row_type = type(current_row).__name__
        next_row_type = type(next_row).__name__ if next_row else 'None'

        # --- Obstacle Proximity Calculation --- 
        
        # Distance Quantization Bins (Lower value = closer/more dangerous)
        # Bin 0: Very Close / Overlap (within ~35px center-to-center for typical obstacles)
        # Bin 1: Close (35px to 60px)
        # Bin 2: Medium (60px to VIEW_DISTANCE_X=80px)
        # Bin 3: Far / None (>= VIEW_DISTANCE_X)
        DIST_BINS = [35, 60, VIEW_DISTANCE_X]
        DEFAULT_DIST_BIN = len(DIST_BINS) # Bin 3 for Far/None

        def quantize_distance(dist):
            for i, threshold in enumerate(DIST_BINS):
                if dist < threshold:
                    return i
            return DEFAULT_DIST_BIN

        # Initialize distances to maximum / furthest bin
        dist_left_bin = DEFAULT_DIST_BIN
        dist_right_bin = DEFAULT_DIST_BIN
        dist_ahead_bin = DEFAULT_DIST_BIN
        dist_behind_bin = DEFAULT_DIST_BIN

        min_dist_left = float('inf')
        min_dist_right = float('inf')
        min_dist_ahead = float('inf')
        min_dist_behind = float('inf')

        # Check Current Row (Left/Right)
        if current_row and hasattr(current_row, 'children'):
            for obs in current_row.children:
                obs_x = obs.pos[0]
                relative_x = obs_x - player_x
                dist_x = abs(relative_x)
                
                # Check distance based on centers for quantization
                if 0 < relative_x < VIEW_DISTANCE_X: # Obstacle to the right
                    min_dist_right = min(min_dist_right, dist_x)
                elif -VIEW_DISTANCE_X < relative_x <= 0: # Obstacle to the left (or overlap)
                    min_dist_left = min(min_dist_left, dist_x)
            
            dist_left_bin = quantize_distance(min_dist_left)
            dist_right_bin = quantize_distance(min_dist_right)

        # Check Next Row (Ahead)
        if next_row and hasattr(next_row, 'children'):
            landing_x = player_x # Assume moving UP doesn't change x
            for obs in next_row.children:
                obs_x = obs.pos[0]
                relative_x_landing = obs_x - landing_x
                dist_x_landing = abs(relative_x_landing)
                min_dist_ahead = min(min_dist_ahead, dist_x_landing)
            dist_ahead_bin = quantize_distance(min_dist_ahead)

        # Check Previous Row (Behind)
        if prev_row and hasattr(prev_row, 'children'):
             target_x_down = player_x + DX[DIRECTION_DOWN] * player.MOVE_DISTANCE
             for obs in prev_row.children:
                 obs_x = obs.pos[0]
                 relative_x_behind = obs_x - target_x_down
                 dist_x_behind = abs(relative_x_behind)
                 min_dist_behind = min(min_dist_behind, dist_x_behind)
             dist_behind_bin = quantize_distance(min_dist_behind)

        # --- Discretize State Components --- 
        player_x_bin = min(int(player_x / (WIDTH / X_BINS)), X_BINS - 1)
        on_cooldown = player.jump_cooldown > 0 
                    
        # --- Final State Tuple --- 
        state = (
            player_x_bin,          # Horizontal position bin (0-9)
            current_row_type,      # Type of current row (String)
            next_row_type,         # Type of row ahead (String)
            on_cooldown,           # Action cooldown active? (Bool)
            # Quantized distances (0=Closest, 3=Farthest/None)
            dist_left_bin,         # Nearest obstacle left (current row)
            dist_right_bin,        # Nearest obstacle right (current row)
            dist_ahead_bin,        # Nearest obstacle ahead (next row)
            dist_behind_bin,       # Nearest obstacle behind (prev row)
        )
        return state

    def choose_action(self, state):
        """Chooses an action using epsilon-greedy policy."""
        if state is None: # Handle invalid states
             return self.random.choice(self.actions) # Default random action
             
        # Add occasional exploration burst to escape local maxima
        if self.total_steps % 100 == 0 and len(self.scores_history) > 10:
            recent_max = max(self.scores_history[-10:])
            if recent_max < 0.5 * self.best_score and self.best_score > 30:
                # If we're stuck in a local maximum, temporarily increase exploration
                exploration_boost = 0.2
                if self.random.uniform(0, 1) < exploration_boost:
                    return self.random.choice(self.actions)
        
        if self.random.uniform(0, 1) < self.epsilon:
            # Explore: choose a random action
            action = self.random.choice(self.actions)
        else:
            # Exploit: choose the best action from Q-table
            q_values = self.q_table[state]
            # Find action with max Q-value, break ties randomly
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]
            action = self.random.choice(best_actions)
            
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        return action

    def learn(self, state, action, reward, next_state, done):
        """Updates the Q-table using the Q-learning rule with experience replay."""
        if state is None or next_state is None:
            return # Cannot learn from invalid states

        # Store experience
        self.experience_buffer.append((state, action, reward, next_state, done))
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0) # Remove oldest experience

        # Only start learning after buffer has enough samples
        if len(self.experience_buffer) < self.batch_size:
            return

        # Sample a random batch from the buffer
        batch = self.random.sample(self.experience_buffer, self.batch_size)

        # Update Q-values for each sample in the batch
        for s, a, r, ns, d in batch:
            # Enhanced Q-learning update rule with optimistic initialization
            # Q(s, a) = Q(s, a) + alpha * (reward + gamma * max(Q(s', a')) - Q(s, a))
            
            # Best Q-value for the next state (ns)
            next_q_values = self.q_table[ns]
            max_next_q = 0.0
            if next_q_values: # Ensure next_state has entries
                max_next_q = max(next_q_values.values())

            # Current Q-value
            current_q = self.q_table[s][a]

            # Calculate target Q-value
            # If the episode ended (done=True), the future reward is just the immediate reward
            target_q = r if d else r + self.gamma * max_next_q

            # Update Q-value with dynamic learning rate
            # Use a higher learning rate for states we haven't visited much
            state_visit_count = self.state_visits.get(s, 0) + 1
            self.state_visits[s] = state_visit_count
            
            # Adjust learning rate based on visit count (higher for less visited states)
            adjusted_alpha = max(self.alpha, self.alpha * 5.0 / state_visit_count)
            
            # Update Q-value with the adjusted learning rate
            new_q = current_q + adjusted_alpha * (target_q - current_q)
            self.q_table[s][a] = new_q
            
            # Add small random noise to Q-values to break symmetry
            if state_visit_count < 10 and self.random.random() < 0.1:
                exploration_noise = self.random.uniform(-0.1, 0.1)
                self.q_table[s][a] += exploration_noise
        
        # Update overall agent statistics if the original transition was terminal
        if done:
            # This update_stats call should be handled by the main game loop
            pass
        