from actors import MyActor
from states import PlayerState
from constants import WIDTH, DX, DY, DIRECTION_WAIT, HEIGHT, DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, WAIT_TIME
from rows import Grass, Road, Dirt, Pavement
from actors import Eagle
import pygame
from utils import key_just_pressed
from dqn_agent import DQNAgent # Import DQNAgent

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
    
    def _ai_decide(self, current_row, next_row):
        direction = None
        
        if isinstance(next_row, Grass):
            direction = 0
            
            
        if isinstance(current_row, Grass):
            if self.x > WIDTH / 2:
                direction = 3 
            elif self.x < WIDTH / 2:
                direction = 1
            else:
                direction = 0
            
        def _ai_decide(self, current_row, next_row):
            direction = None
            
            if isinstance(next_row, Grass):
                direction = 0
                
                
            if isinstance(current_row, Grass):
                if self.x > WIDTH / 2:
                    direction = 3 
                elif self.x < WIDTH / 2:
                    direction = 1
                else:
                    direction = 0
                
            if isinstance(next_row, Road): 
            # 1. Check if there are cars on the row 
            # 2. check if distance from a car to player is safe if yes move forward
            # 3. if not safe, either do nothing or pick next safe direction. Next safe direction means either left, right, forward or backwoard from current posithion where there are no obstacles/enemies. 
                if len(next_row.children) == 0:
                    direction = 0
                
                else:    
                    for rowindex in range(len(next_row.children)):
                        object_pos = next_row.children[rowindex].pos
                        object_x = object_pos[0]
                        next_car = next_row.children[rowindex]
                    
                        if abs(self.x - object_x) > 90:
                            direction = 0
                        elif next_car.dx == 1 and abs(self.x - object_x) < 75 :#and abs(self.x - current_object_x) > 50: 
                            direction = 3
                        elif next_car.dx == -1 and abs(self.x - object_x) < 75 :#and abs(self.x - current_object_x) > 50:
                            direction = 1
                        elif next_car.dx == -1 and self.x > object_x and abs(self.x - object_x) < 75:
                            direction = 0
                        elif next_car.dx == 1 and self.x < object_x and abs(self.x - object_x) < 75:
                            direction = 0
                        elif len(next_row.children) == 0:
                            direction = 0
                        elif self.y > 750:
                            direction = 4
                        else:
                            direction = 4
                            
                        for currentrowindex in range(len(current_row.children)):
                            current_object_pos = current_row.children[currentrowindex].pos
                            current_object_x = current_object_pos[0]
                            current_car = current_row.children[currentrowindex]
                            
                            if abs(self.x - current_object_x) < 90:
                                if current_car.dx == 1:
                                    direction = 1
                                if current_car.dx == -1:
                                    direction = 3  
                            if len(current_row.children) == 0:
                                direction = 0

            # if isinstance(next_row, Rail):
            #     if len(next_row.children) == 0:
            #         direction = 0
            #     else:
            #         direction = 4
            #         self.jump_cooldown = 10
            #         direction = 0
                
                # if Rail.train_incoming:
                #     jump_cooldown += 150
                #     direction = 0
                # else:
                #     direction = 0
                
                
                # if Rail.index.update.index == 1:
                #     direction = 0
                # else:
                #     direction = 4

                
                
            if isinstance(next_row, Pavement):
                direction = 0
                
            if isinstance(current_row, Pavement):
                if self.x > WIDTH / 2:
                    direction = 3 
                elif self.x < WIDTH / 2:
                    direction = 1
                else:
                    direction = 0
                
            if isinstance(next_row, Dirt):
                direction = 0
                
            if direction is None:
                direction = 0

            return direction


    def calculate_reward(self, action_resulted_in_death, action_was_wait, 
                         action_moved_sideways, action_moved_backwards, 
                         progress_made, new_record, attempted_invalid_move):
        """
        Calculates the reward based on the outcome of the last action.
        Prioritizes Survival: Small bonus per step alive, reduced penalties for safe moves.
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
        # --- Survival-Focused Rewards --- 
        DEATH_PENALTY = -1000.0  # Keep extremely high
        SURVIVAL_BONUS = 0.1    # Small reward for each step survived
        FORWARD_REWARD = 20.0    # Reduced reward for forward progress (still good, but less emphasis)
        PROGRESS_REWARD = 5.0    # Reduced reward for any upward movement
        # TIME_PENALTY = -0.1    # Optional: Very small time penalty, or remove completely
        WAIT_PENALTY = 0.0       # No penalty for waiting (might be strategic)
        SIDEWAYS_PENALTY = 0.0   # No penalty for sideways movement (might be strategic)
        BACKWARDS_PENALTY = -20.0 # Keep high penalty for moving backwards
        INVALID_MOVE_PENALTY = -10.0 # Keep penalty for attempting invalid moves

        if action_resulted_in_death:
            return DEATH_PENALTY

        # Start with survival bonus instead of time penalty
        reward = SURVIVAL_BONUS

        if new_record:
            reward += FORWARD_REWARD # Bonus for new record
        elif progress_made: # Moved forward but not a new record
             reward += PROGRESS_REWARD
        elif action_moved_backwards:
             reward += BACKWARDS_PENALTY
        elif action_moved_sideways:
             reward += SIDEWAYS_PENALTY # Now 0
        elif action_was_wait:
             reward += WAIT_PENALTY # Now 0
        elif attempted_invalid_move:
             reward += INVALID_MOVE_PENALTY

        return reward
    
    def update(self):
        from game import game # Import game locally
        from main import state as game_mode, State # Import game mode (MANUAL/AUTO)
        
        agent = game.agent # Get the current agent from the game object
        
        # Variable to store if the last attempted move was invalid
        last_move_was_invalid = False # This needs to be tracked across frames ideally

        # --- Store state BEFORE action/update ---
        y_before_update = self.y
        min_y_before_update = self.min_y
        state_before_update = self.state 

        # --- Learning Step (Learn from the PREVIOUS action's outcome) ---
        # Check if we are in an agent-controlled mode and have necessary history
        is_agent_mode = (game_mode == State.AUTO_QLEARN or game_mode == State.AUTO_DQN)
        if is_agent_mode and self.last_state_for_learning is not None and agent is not None:
            # Determine the outcome of the previous action (which led to the current state)
            action_resulted_in_death = (state_before_update != PlayerState.ALIVE)
            progress_made = (y_before_update < self.prev_y) # Compare current y with y *before* the last action
            new_record = progress_made and (y_before_update < min_y_before_update) # Check against min_y *before* update too
            action_was_wait = (self.last_action_for_learning == DIRECTION_WAIT)
            action_moved_sideways = (self.last_action_for_learning == DIRECTION_LEFT or self.last_action_for_learning == DIRECTION_RIGHT) and not progress_made and y_before_update == self.prev_y
            action_moved_backwards = (self.last_action_for_learning == DIRECTION_DOWN) and (y_before_update > self.prev_y)
            # We need info about whether the *previous* action attempt failed.
            # last_move_was_invalid from *this* frame is not correct here.
            # For now, we pass False, as tracking across frames isn't implemented.
            attempted_invalid_move = False # Placeholder - needs proper tracking
            
            # Calculate reward based on the outcome
            reward = self.calculate_reward(
                action_resulted_in_death, 
                action_was_wait,
                action_moved_sideways,
                action_moved_backwards,
                progress_made, 
                new_record,
                attempted_invalid_move # Pass the result from the *previous* frame's attempt
            )
            
            # Get the current state S' (after the last action resolved)
            current_state_features = agent.get_state(self, game) # This is S' for the (S,A,R,S') tuple

            # Learn from the experience (S, A, R, S', Done)
            # S = self.last_state_for_learning (state before action A was taken)
            # A = self.last_action_for_learning (action taken)
            # R = reward (calculated above based on outcome)
            # S'= current_state_features (state after action A resolved)
            # Done = action_resulted_in_death
            
            # For DQN, S and S' need to be tensors. `last_state_for_learning` should store the tensor.
            # `current_state_features` from agent.get_state() should return a tensor for DQN.
            state_to_learn_from = self.last_state_for_learning
            action_learned = self.last_action_for_learning
            
            # Ensure the agent's learn method handles potential None states
            # The learn method in both agents should already do this
            if isinstance(agent, DQNAgent):
                # DQNAgent expects learn() with no args, using memory buffer
                # It needs the transition pushed to memory earlier
                # Let's push to memory here, just before potentially calling learn()
                # Note: Pushing requires state, action, next_state, reward, done
                # Ensure state_to_learn_from and current_state_features are valid tensors
                if state_to_learn_from is not None and current_state_features is not None: 
                    agent.memory.push(state_to_learn_from, action_learned, current_state_features, reward, action_resulted_in_death)
                    agent.learn() # DQN learns from batch sampled from memory
                # else: 
                    # print("Skipping DQN push/learn due to None state.") # Debug
            else: # Assuming QLearningAgent
                 agent.learn(state_to_learn_from, action_learned, reward, current_state_features, action_resulted_in_death)

            # If player died, reset the learning state variables for the next episode
            if action_resulted_in_death:
                self.last_state_for_learning = None
                self.last_action_for_learning = None
            # Else, the current state becomes the starting state for the *next* cycle
            # This is handled below where last_state_for_learning is updated after choosing the *next* action.

        # --- Handle Input / AI Action Selection (Choose action for the CURRENT step) ---
        is_ready_for_action = (self.timer == 0 and self.jump_cooldown == 0 and self.state == PlayerState.ALIVE)
        action_to_take = None
        move_attempted_this_frame = False
        move_succeeded_this_frame = True # Assume success unless attempted and failed

        if is_ready_for_action:
            if game_mode == State.MANUAL:
                if self.input_queue:
                    action_to_take = self.input_queue.pop(0)
                # Clear learning state when in manual mode
                self.last_state_for_learning = None
                self.last_action_for_learning = None

            elif is_agent_mode: # Covers AUTO_QLEARN and AUTO_DQN
                 if agent is not None:
                     # Get current state S for decision making
                     current_state_features = agent.get_state(self, game)
                     
                     if current_state_features is not None:
                         # Choose action A based on state S
                         action_to_take = agent.choose_action(current_state_features)
                         
                         # Store S (current_state_features) and A (action_to_take)
                         # to be used in the *next* learning step (after this action executes).
                         self.last_state_for_learning = current_state_features # Store S (potentially tensor)
                         self.last_action_for_learning = action_to_take       # Store A
                     else:
                          # Handle invalid state - maybe wait or random?
                          action_to_take = DIRECTION_WAIT 
                          self.last_state_for_learning = None # Cannot learn from this
                          self.last_action_for_learning = None
                 else:
                     action_to_take = DIRECTION_WAIT # Agent not available
                     self.current_action_str = "N/A" # Reset action string if no agent

        # --- Execute Chosen Action ---
        if action_to_take is not None:
            # --- Action String Update ---
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
            else:
                # Attempt movement action
                move_succeeded_this_frame = self.handle_input(action_to_take)
                move_attempted_this_frame = True
                # Set the standard jump cooldown regardless of whether move succeeded
                self.jump_cooldown = self.JUMP_COOLDOWN

        # Store if the move attempted THIS frame was invalid. This state is needed for the *next* frame's reward calc.
        # This is tricky. The `last_move_was_invalid` variable check in the learning step needs the value
        # from the *previous* frame. Let's add an instance variable to store this.
        # We set `self._last_move_invalid` here, and read it at the START of the *next* update cycle.
        self._last_move_invalid_internal = move_attempted_this_frame and not move_succeeded_this_frame

        # --- Manual Input Queueing (Always allow queueing) ---
        if key_just_pressed(pygame.K_UP): self.input_queue.append(DIRECTION_UP)
        if key_just_pressed(pygame.K_RIGHT): self.input_queue.append(DIRECTION_RIGHT)
        if key_just_pressed(pygame.K_DOWN): self.input_queue.append(DIRECTION_DOWN)
        if key_just_pressed(pygame.K_LEFT): self.input_queue.append(DIRECTION_LEFT)
        
        if self.state == State.AUTO:        
                if self.timer == 0 and self.jump_cooldown == 0:
                    try:
                        dir = self._ai_decide(current_row, next_row)
                        if dir != DIRECTION_WAIT:
                            self.handle_input(dir)  
                            self.jump_cooldown = self.JUMP_COOLDOWN
                        
                    except Exception as exp:
                        print(exp)
        
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
