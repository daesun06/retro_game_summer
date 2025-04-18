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
    def __init__(self, actions):
        self.actions = actions
        self.alpha = ALPHA
        self.gamma = GAMMA
        self.epsilon = EPSILON_START
        self.epsilon_decay = EPSILON_DECAY
        self.epsilon_min = EPSILON_MIN
        
        # Use defaultdict for convenient Q-table initialization
        self.q_table = self.load_q_table()
        
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

    def load_q_table(self):
        if os.path.exists(Q_TABLE_FILE):
            try:
                with open(Q_TABLE_FILE, 'rb') as f:
                    q_table = pickle.load(f)
                    print(f"Loaded Q-table with {len(q_table)} states.")
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
                # Convert back to regular dict for pickling if needed, though defaultdict should pickle fine
                pickle.dump(dict(self.q_table), f) 
                print(f"Saved Q-table with {len(self.q_table)} states.")
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
        Calculates a discrete state representation based on the player and game environment.
        Args:
            player: The Bunner instance.
            game: The Game instance.
        Returns:
            A tuple representing the discrete state, or None if state is invalid.
        """
        # Constants for state discretization
        X_BINS = 10  # Increased horizontal bins for more granularity
        VIEW_DISTANCE_X = 80 # How far left/right to check for obstacles
        VIEW_DISTANCE_Y = player.MOVE_DISTANCE * 2 # How far ahead/behind to check (e.g., 2 rows)
        OBSTACLE_PROXIMITY_THRESHOLD = 30 # Closer than this is considered immediate danger
        
        player_x = player.x
        player_y = player.y
        player_width_half = 16 # Assuming player is ~32px wide

        # Find player's current row and nearby rows
        current_row = None
        next_row = None
        prev_row = None
        rows_in_view = {} # Store rows by their Y coordinate for quick lookup
        target_y_up = player_y + DY[DIRECTION_UP] * player.MOVE_DISTANCE
        target_y_down = player_y + DY[DIRECTION_DOWN] * player.MOVE_DISTANCE

        for i, row in enumerate(game.rows):
            rows_in_view[row.y] = row
            if row.y == player_y:
                current_row = row
            elif row.y == target_y_up:
                next_row = row
            elif row.y == target_y_down:
                 prev_row = row # Row player would move to if going DOWN
        
        if current_row is None:
            return None # Invalid state if not on a row

        current_row_type = type(current_row).__name__
        next_row_type = type(next_row).__name__ if next_row else 'None'
        # prev_row_type = type(prev_row).__name__ if prev_row else 'None' # Optionally add previous row type

        # --- Obstacle Detection --- 
        danger_close_left = False
        danger_close_right = False
        danger_far_left = False
        danger_far_right = False
        danger_behind = False # Danger on the row behind (if moving back)
        danger_landing_zone = False # Direct overlap on landing spot (moving UP)
        danger_landing_zone_sides = False # Danger near landing spot (moving UP)
        obstacle_moving_towards_left = False # Obstacle on current row moving left nearby
        obstacle_moving_towards_right = False # Obstacle on current row moving right nearby

        # Helper to check obstacle proximity
        def check_obstacles(row, check_y):
            nonlocal danger_close_left, danger_close_right, danger_far_left, danger_far_right
            nonlocal obstacle_moving_towards_left, obstacle_moving_towards_right
            if row and hasattr(row, 'children'):
                for obs in row.children:
                    obs_x = obs.pos[0]
                    obs_width_half = getattr(obs, 'width', 32) / 2
                    relative_x = obs_x - player_x
                    distance_x = abs(relative_x)
                    overlap_threshold = player_width_half + obs_width_half

                    # Check horizontal proximity relative to player on the *same row*
                    if row.y == player_y:
                        # Moving towards player?
                        obs_dx = getattr(obs, 'dx', 0)
                        if obs_dx < 0 and 0 < relative_x < VIEW_DISTANCE_X: # Moving left towards player from right
                            obstacle_moving_towards_left = True
                        if obs_dx > 0 and -VIEW_DISTANCE_X < relative_x < 0: # Moving right towards player from left
                             obstacle_moving_towards_right = True
                             
                        # General proximity checks
                        if 0 < relative_x < VIEW_DISTANCE_X: # Obstacle to the right
                            danger_far_right = True
                            if distance_x < overlap_threshold + OBSTACLE_PROXIMITY_THRESHOLD:
                                 danger_close_right = True
                        elif -VIEW_DISTANCE_X < relative_x <= 0: # Obstacle to the left (or overlapping)
                            danger_far_left = True
                            if distance_x < overlap_threshold + OBSTACLE_PROXIMITY_THRESHOLD:
                                danger_close_left = True

        # Check current row
        check_obstacles(current_row, player_y)

        # Check row behind (where player might move if going DOWN)
        if prev_row and hasattr(prev_row, 'children'):
             target_x_down = player_x + DX[DIRECTION_DOWN] * player.MOVE_DISTANCE
             for obs in prev_row.children:
                 obs_x = obs.pos[0]
                 obs_width_half = getattr(obs, 'width', 32) / 2
                 # Check if moving DOWN would land on an obstacle
                 if abs(obs_x - target_x_down) < (player_width_half + obs_width_half):
                     danger_behind = True
                     break

        # Check next row (landing zone for moving UP)
        if next_row and hasattr(next_row, 'children'):
            landing_x = player_x + DX[DIRECTION_UP] * player.MOVE_DISTANCE # Should be same as player_x
            landing_zone_width = player_width_half * 2 # Approximate width needed
            for obs in next_row.children:
                obs_x = obs.pos[0]
                obs_width_half = getattr(obs, 'width', 32) / 2
                relative_x_landing = obs_x - landing_x
                distance_x_landing = abs(relative_x_landing)
                overlap_threshold = player_width_half + obs_width_half

                # Check direct overlap
                if distance_x_landing < overlap_threshold:
                    danger_landing_zone = True
                
                # Check proximity to the sides of the landing zone
                if overlap_threshold <= distance_x_landing < overlap_threshold + VIEW_DISTANCE_X / 2: # Check slightly wider than overlap
                    danger_landing_zone_sides = True
                    
                # No need to check further if both flags are true
                if danger_landing_zone and danger_landing_zone_sides:
                    break

        # --- Discretize State Components --- 
        player_x_bin = min(int(player_x / (WIDTH / X_BINS)), X_BINS - 1)
        # Maybe add player's jump cooldown state?
        # on_cooldown = player.jump_cooldown > 0
                    
        # State tuple - ensures hashability
        state = (
            player_x_bin,
            current_row_type,
            next_row_type,
            # Current row dangers:
            danger_close_left,
            danger_close_right,
            danger_far_left, # Maybe combine close/far later if state space too large
            danger_far_right,
            obstacle_moving_towards_left, 
            obstacle_moving_towards_right,
            # Next row dangers (landing zone):
            danger_landing_zone,
            danger_landing_zone_sides,
            # Prev row danger:
            danger_behind,
            # Cooldown status? 
            # on_cooldown 
        )
        return state

    def choose_action(self, state):
        """Chooses an action using epsilon-greedy policy."""
        if state is None: # Handle invalid states
             return self.random.choice(self.actions) # Default random action
             
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

    def learn(self, state, action, reward, next_state):
        """Updates the Q-table using the Q-learning rule."""
        if state is None or next_state is None:
            return # Cannot learn from invalid states

        # Store experience for potential replay
        self.experience_buffer.append((state, action, reward, next_state))
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
            
        # Q-learning update rule:
        # Q(s, a) = Q(s, a) + alpha * (reward + gamma * max(Q(s', a')) - Q(s, a))
        
        # Best Q-value for the next state
        next_q_values = self.q_table[next_state]
        max_next_q = 0.0
        if next_q_values: # Ensure next_state has entries
             max_next_q = max(next_q_values.values())

        # Current Q-value
        current_q = self.q_table[state][action]

        # Update Q-value
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
        
        # Check if player died and update stats
        from states import PlayerState
        if reward <= -500:  # Large negative reward indicates death
            self.update_stats(0, is_death=True)
        