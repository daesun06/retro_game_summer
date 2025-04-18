from actors import MyActor
from states import PlayerState
from constants import WIDTH, DX, DY, DIRECTION_WAIT, HEIGHT, DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, WAIT_TIME
from actors import Eagle
import pygame
from utils import key_just_pressed

# Q-learning related imports - We'll get agent from game object
# from q_learning import QLearningAgent 

class Bunner(MyActor):
    MOVE_DISTANCE = 10
    JUMP_COOLDOWN = 15 # Slightly reduced cooldown for potentially faster learning/playing
    WAIT_COOLDOWN = 5  # Shorter cooldown after waiting

    def __init__(self, pos):
        super().__init__("blank", pos)
        self.state = PlayerState.ALIVE
        self.direction = 2 # Start facing down
        self.timer = 0
        self.jump_cooldown = 0
        self.input_queue = []
        # Keeps track of the furthest distance we've reached so far in the level, for scoring
        # (Level Y coordinates decrease as the screen scrolls)
        self.min_y = self.y

        # Q-learning state variables
        self.last_state_for_learning = None
        self.last_action_for_learning = None
        self.prev_y = self.y # Store y before the last action
        self.current_action_str = "N/A" # For displaying current action

    def handle_input(self, dir):
        from game import game # Import game here to avoid circular imports

        # Prevent movement into invalid directions (e.g., off-screen)
        target_x = self.x + Bunner.MOVE_DISTANCE * DX[dir]
        target_y = self.y + Bunner.MOVE_DISTANCE * DY[dir]

        if not (0 <= target_x <= WIDTH): # Basic boundary check for X
             # print(f"Prevented move: X boundary ({target_x})")
             return False # Indicate move failed

        target_row = None
        for row in game.rows:
            # Find the row corresponding to the target Y coordinate
            if row.y == target_y:
                 target_row = row
                 break
                 
        if target_row is not None:
            # Can the player move to the new location on the target row?
            if target_row.allow_movement(target_x):
                self.direction = dir
                self.timer = Bunner.MOVE_DISTANCE
                # Play sound only if not muted (will be handled in game.play_sound)
                game.play_sound("jump", 1)
                return True # Indicate move succeeded
            # else:
                # print(f"Prevented move: Obstacle or disallowed on row {type(target_row).__name__} at x={target_x}")
        # else:
             # print(f"Prevented move: Target row at y={target_y} not found")
        
        return False # Indicate move failed

    def calculate_reward(self, action_resulted_in_death, action_was_wait, 
                         action_moved_sideways, action_moved_backwards, 
                         progress_made, new_record, attempted_invalid_move):
        """
        Calculates the reward based on the outcome of the last action.
        Args:
            action_resulted_in_death (bool): True if the player died as a result of the last action.
            action_was_wait (bool): True if the last action was WAIT.
            action_moved_sideways (bool): True if the last action was LEFT or RIGHT.
            action_moved_backwards (bool): True if the last action was DOWN.
            progress_made (bool): True if the player moved UP (y decreased).
            new_record (bool): True if the player reached a new minimum y.
            attempted_invalid_move (bool): True if the player tried to move into an obstacle or off-screen.
        Returns:
            float: The calculated reward value.
        """
        DEATH_PENALTY = -1000  # Significantly increased penalty for death
        FORWARD_REWARD = 50    # Major reward for moving forward and setting a new record
        PROGRESS_REWARD = 10   # Solid reward for any upward movement
        TIME_PENALTY = -0.5    # Increased penalty per step to encourage efficiency
        WAIT_PENALTY = -5      # Higher penalty for waiting (doing nothing)
        SIDEWAYS_PENALTY = -3  # Moderate penalty for sideways movement
        BACKWARDS_PENALTY = -20 # Severe penalty for moving backwards
        INVALID_MOVE_PENALTY = -10 # Serious penalty for attempting invalid moves

        if action_resulted_in_death:
            return DEATH_PENALTY

        reward = TIME_PENALTY # Start with time penalty

        if new_record:
            reward += FORWARD_REWARD # Significant bonus for new record
        elif progress_made: # Moved forward but not a new record
             reward += PROGRESS_REWARD
        elif action_moved_backwards:
             reward += BACKWARDS_PENALTY
        elif action_moved_sideways:
             reward += SIDEWAYS_PENALTY
        elif action_was_wait:
             reward += WAIT_PENALTY
        elif attempted_invalid_move:
             reward += INVALID_MOVE_PENALTY

        return reward
    
    def update(self):
        from game import game # Import game locally
        from main import state as game_mode, State # Import game mode (MANUAL/AUTO)
        
        agent = game.agent # Get the Q-learning agent from the game object
        
        # Variable to store if the last attempted move was invalid
        last_move_was_invalid = False 

        # --- Store state BEFORE action/update ---
        y_before_update = self.y
        min_y_before_update = self.min_y
        state_before_update = self.state 

        # --- Q-Learning Step (Learn from the PREVIOUS action's outcome) ---
        # This must happen *before* the next action is chosen, using the result of the last S,A pair.
        if game_mode == State.AUTO and self.last_state_for_learning is not None and agent is not None:
            # Determine the outcome of the previous action (which led to the current state)
            action_resulted_in_death = (state_before_update != PlayerState.ALIVE)
            progress_made = (y_before_update < self.prev_y) # Compare current y with y *before* the last action
            new_record = progress_made and (y_before_update < min_y_before_update) # Check against min_y *before* update too
            action_was_wait = (self.last_action_for_learning == DIRECTION_WAIT)
            action_moved_sideways = (self.last_action_for_learning == DIRECTION_LEFT or self.last_action_for_learning == DIRECTION_RIGHT) and not progress_made and y_before_update == self.prev_y
            action_moved_backwards = (self.last_action_for_learning == DIRECTION_DOWN) and (y_before_update > self.prev_y)
            # We need info about whether the *previous* action attempt failed.
            # This requires storing the success/failure status from the previous frame's handle_input call.
            # Let's approximate this for now by checking if a move action was taken but y didn't change appropriately.
            # A better approach would be to store the return value of handle_input from the previous step.
            # We'll pass `last_move_was_invalid` which we set *after* handle_input below.
            
            # Calculate reward based on the outcome
            reward = self.calculate_reward(
                action_resulted_in_death, 
                action_was_wait,
                action_moved_sideways,
                action_moved_backwards,
                progress_made, 
                new_record,
                last_move_was_invalid # Pass the result from the *previous* frame's attempt
            )
            
            # Get the current state S' (after the last action resolved)
            current_state_features = agent.get_state(self, game)

            # Learn from the experience (S, A, R, S')
            agent.learn(self.last_state_for_learning, self.last_action_for_learning, reward, current_state_features)

            # If player died, reset the learning state variables for the next episode
            if action_resulted_in_death:
                self.last_state_for_learning = None
                self.last_action_for_learning = None
                # print("Player died, resetting learning state.")
            
            # Important: Only update prev_y *after* using it for reward calculation for the previous step
            # We'll update it before the *next* action is taken below.


        # --- Handle Input / AI Action Selection (Choose action for the CURRENT step) ---
        is_ready_for_action = (self.timer == 0 and self.jump_cooldown == 0 and self.state == PlayerState.ALIVE)
        action_to_take = None

        if is_ready_for_action:
            if game_mode == State.MANUAL:
                if self.input_queue:
                    action_to_take = self.input_queue.pop(0)
                # Clear learning state when in manual mode
                self.last_state_for_learning = None
                self.last_action_for_learning = None

            elif game_mode == State.AUTO:
                 if agent is not None:
                     # Get current state S for decision making
                     current_state_features = agent.get_state(self, game)
                     
                     if current_state_features is not None:
                         # Choose action A based on state S
                         action_to_take = agent.choose_action(current_state_features)
                         
                         # Store S and A to be used in the *next* learning step (after this action executes)
                         self.last_state_for_learning = current_state_features
                         self.last_action_for_learning = action_to_take
                         # print(f"Q-Learn State: {current_state_features}, Action Chosen: {action_to_take}")
                     else:
                          # Handle invalid state - maybe wait or random?
                          action_to_take = DIRECTION_WAIT 
                          self.last_state_for_learning = None # Cannot learn from this
                          self.last_action_for_learning = None
                          # print("Q-Learn: Invalid state detected, choosing WAIT.")
                 else:
                     action_to_take = DIRECTION_WAIT # Agent not available
                     self.current_action_str = "N/A" # Reset action string if no agent
                     # print("Q-Learn: Agent not found, choosing WAIT.")

        # --- Execute Chosen Action ---
        move_attempted = False
        move_succeeded = True # Assume success unless move attempted and failed
        if action_to_take is not None:
            # --- Action String Update ---
            # Map the chosen action to a string for display
            action_map = { 
                DIRECTION_UP: "UP", DIRECTION_DOWN: "DOWN", 
                DIRECTION_LEFT: "LEFT", DIRECTION_RIGHT: "RIGHT", 
                DIRECTION_WAIT: "WAIT"
            }
            self.current_action_str = action_map.get(action_to_take, "N/A")
            
            # Store current y *before* executing the chosen action. This becomes prev_y for the *next* reward calculation.
            self.prev_y = self.y 
            
            if action_to_take == DIRECTION_WAIT:
                self.timer = WAIT_TIME # Stay idle
                self.jump_cooldown = self.WAIT_COOLDOWN # Shorter cooldown
                # print("Action: WAIT")
            else:
                # Attempt movement action
                move_succeeded = self.handle_input(action_to_take)
                move_attempted = True
                # Set the standard jump cooldown regardless of whether move succeeded
                # Agent needs to learn not to attempt invalid moves
                self.jump_cooldown = self.JUMP_COOLDOWN
                # print(f"Action: {action_to_take}, Succeeded: {move_succeeded}, Timer: {self.timer}")

        # Store if the move attempted THIS frame was invalid, for the NEXT frame's reward calculation
        last_move_was_invalid = move_attempted and not move_succeeded

        # --- Manual Input Queueing (Always allow queueing) ---
        if key_just_pressed(pygame.K_UP): self.input_queue.append(DIRECTION_UP)
        if key_just_pressed(pygame.K_RIGHT): self.input_queue.append(DIRECTION_RIGHT)
        if key_just_pressed(pygame.K_DOWN): self.input_queue.append(DIRECTION_DOWN)
        if key_just_pressed(pygame.K_LEFT): self.input_queue.append(DIRECTION_LEFT)
        
        # --- Update Cooldowns ---
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
            
        # --- Update Player Movement & State (Physics, Collision) ---
        landed_this_frame = False
        if self.timer > 0:
        # Apply movement if timer is active (from a successful handle_input call)
            self.x += DX[self.direction]
            self.y += DY[self.direction]
            self.timer -= 1
            if self.timer == 0:
                 landed_this_frame = True # Just finished movement sequence
                
        # --- Collision Checks and Row Interactions ---
        if self.state == PlayerState.ALIVE: # Only check collisions if alive
            current_row = None
            for row in game.rows:
                if row.y == self.y:
                    current_row = row
                    break

            if current_row:
                collision_state, dead_obj_y_offset = current_row.check_collision(self.x)
                
                if collision_state != PlayerState.ALIVE:
                    self.state = collision_state
                    # print(f"Collision! New state: {self.state}")
                    if self.state == PlayerState.SPLAT:
                        game.actors.insert(0, MyActor("splat" + str(self.direction), (self.x, dead_obj_y_offset)))
                    self.timer = 100 # Use timer for death pause/animation
                else:
                    # Still alive on this row
                    self.x += current_row.push() # Apply push force (logs)
                    if landed_this_frame:
                        current_row.play_sound() # Play landing sound
            else:
                 # Player is not on a valid row (e.g., mid-jump, or somehow off-grid)
                 # Check if fallen too far back
                if self.y > game.scroll_pos + HEIGHT + 80:
                     # print("Fell off bottom!")
                    game.eagle = Eagle((self.x, game.scroll_pos))
                    self.state = PlayerState.EAGLE
                    self.timer = 150
                    game.play_sound("eagle")

            self.x = max(16, min(WIDTH - 16, self.x)) # Keep within horizontal bounds
            
        elif self.state != PlayerState.ALIVE: # Player is dead/dying
            # Countdown death timer
            if self.timer > 0: # Only decrement if timer was set (e.g., for splat/splash/eagle)
                self.timer -= 1

        # Update furthest progress AFTER all movement and state changes for the frame
        self.min_y = min(self.min_y, self.y)

        # --- Update Player Image ---
        self.image = "blank"
        if self.state == PlayerState.ALIVE:
            # Show jump anim only if moving *due to a move action* (timer > 0 and not a WAIT action)
            # Need to check if the timer > 0 corresponds to an actual move
            # A simple check: if the last action wasn't WAIT and timer > 0
            is_moving = self.timer > 0 and self.last_action_for_learning != DIRECTION_WAIT 
            if is_moving:
                self.image = "jump" + str(self.direction)
            else: # Idle or finished moving/waiting
                self.image = "sit" + str(self.direction)
        elif self.state == PlayerState.SPLASH and self.timer > 84: # Splash animation uses death timer
            self.image = "splash" + str(int((100 - self.timer) / 2)) 
        # Other states like SPLAT, EAGLE handled elsewhere or have no player image change.
