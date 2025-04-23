import pgzero, pgzrun, pygame, sys, atexit
from enum import Enum
import csv # Added for CSV writing
import os # Added for checking file existence

# Import our modules
from utils import check_python_version, key_just_pressed, display_number, init_random_seeds
from constants import (WIDTH, HEIGHT, TITLE, DIRECTION_UP, DIRECTION_RIGHT, 
                       DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT, RANDOM_SEED)
from states import State, PlayerState
from game import Game
from player import Bunner
from q_learning import QLearningAgent # Import the Q agent
from dqn_agent import DQNAgent # Import the DQN agent
from rows import reset_random_generator as reset_rows_random
from actors import reset_random_generator as reset_actors_random

# Function to reset all random generators
def reset_all_random_generators():
    """Reset all random generators across all modules to ensure consistent starting state"""
    init_random_seeds(RANDOM_SEED)
    reset_rows_random()
    reset_actors_random()
    # No need to print here, happens in init_random_seeds

# Check versions before continuing
check_python_version()

# Initialize random seeds for deterministic environment
reset_all_random_generators() # Initial reset

# Global game state
state = State.MENU
high_score = 0
game = None
# --- Agent Handling ---
q_agent = None # Instance for Q-Learning
dqn_agent = None # Instance for DQN
# Define state size for DQN - MUST MATCH dqn_agent.py's get_state output vector size
# Updated size: 6 numerical + 2 * 7 one-hot = 20
DQN_STATE_SIZE = 20 
active_agent = None # Reference to the currently active agent (q_agent or dqn_agent)
# --- End Agent Handling ---
epoch_count = 0 # Track number of games played/restarts

# Define all possible actions for the agents
ALL_ACTIONS = [DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT]

MAX_SPEED_MULTIPLIER = 200
TARGET_FPS = 60 # Base FPS
STATS_Q_FILENAME = "training_stats_q.csv" # File to save stats (might need agent-specific files later)
STATS_D_FILENAME = 'training_stats.csv'
STATS_SAVE_INTERVAL = 20 # How often to save stats (in epochs)

def load_high_score():
    global high_score
    try:
        with open("high1.txt", "r") as f:
            high_score = int(f.read())
    except:
        high_score = 0

# --- Agent Initialization ---
def initialize_agents():
    """Initializes both Q-learning and DQN agents."""
    global q_agent, dqn_agent
    # Initialize Q-Learning Agent
    q_agent = QLearningAgent(actions=ALL_ACTIONS) 
    print(f"Q-Learning agent initialized.")
    
    # Initialize DQN Agent
    # Ensure DQN_STATE_SIZE matches the output of DQNAgent.get_state() vectorization
    dqn_agent = DQNAgent(actions=ALL_ACTIONS, state_size=DQN_STATE_SIZE) 
    print(f"DQN agent initialized with state size {DQN_STATE_SIZE}.")

def save_agents():
    """Saves the state of both agents if they exist."""
    print("Attempting to save agent states...")
    if q_agent:
        q_agent.save_q_table()
    else:
        print("Q-agent not found, skipping save.")
        
    if dqn_agent:
        dqn_agent.save_model()
    else:
        print("DQN-agent not found, skipping save.")

# Register the save function to be called on exit
atexit.register(save_agents)
# --- End Agent Initialization & Saving ---

def initialize_stats_file():
    """Creates the CSV stats file and writes the header if it doesn't exist."""
    # TODO: Consider agent-specific stat files if needed
    if state == State.AUTO_QLEARN:
        if not os.path.exists(STATS_Q_FILENAME):
            try:
                with open(STATS_Q_FILENAME, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Add agent type column
                    writer.writerow(["Epoch", "AgentType", "Epsilon", "States/Steps", "AvgScore", "BestScore", "TotalDeaths"])
                print(f"Created statistics file: {STATS_Q_FILENAME}")
            except Exception as e:
                print(f"Error creating statistics file {STATS_Q_FILENAME}: {e}")    
    
    elif state == State.AUTO_DQN:
        if not os.path.exists(STATS_D_FILENAME):
            try:
                with open(STATS_D_FILENAME, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Add agent type column
                    writer.writerow(["Epoch", "AgentType", "Epsilon", "States/Steps", "AvgScore", "BestScore", "TotalDeaths"])
                print(f"Created statistics file: {STATS_D_FILENAME}")
            except Exception as e:
                print(f"Error creating statistics file {STATS_D_FILENAME}: {e}")

def save_stats_to_csv():
    """Appends the current active agent's statistics to the CSV file."""
    global epoch_count, active_agent, state
    if not active_agent:
        # print("No active agent, cannot save stats.") # Reduce noise
        return
        
    agent_type = "Q-Learn" if state == State.AUTO_QLEARN else "DQN" if state == State.AUTO_DQN else "N/A"
    
    # Adapt stats based on agent type
    if isinstance(active_agent, QLearningAgent):
        epsilon_val = active_agent.epsilon
        states_or_steps = len(active_agent.q_table) # Number of states
    elif isinstance(active_agent, DQNAgent):
        epsilon_val = active_agent.epsilon
        states_or_steps = active_agent.steps_done # Number of learning steps
    else: # Should not happen if active_agent is set
        return 
        
    stats = [
        epoch_count,
        agent_type,
        f"{epsilon_val:.5f}", # Format epsilon
        states_or_steps,
        f"{active_agent.avg_score:.2f}", # Format average score
        active_agent.best_score,
        active_agent.total_deaths
    ]
    if state == State.AUTO_QLEARN:
        try:
            # Ensure file exists and has header (redundant check, but safe)
            if not os.path.exists(STATS_Q_FILENAME):
                initialize_stats_file()
                
            with open(STATS_Q_FILENAME, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(stats)
            # print(f"Epoch {epoch_count}: Saved {agent_type} stats to {STATS_FILENAME}") # Reduce noise
        except Exception as e:
            print(f"Error writing stats to {STATS_Q_FILENAME}: {e}")
    elif state == State.AUTO_DQN:
        try:
            # Ensure file exists and has header (redundant check, but safe)
            if not os.path.exists(STATS_D_FILENAME):
                initialize_stats_file()
                
            with open(STATS_D_FILENAME, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(stats)
            # print(f"Epoch {epoch_count}: Saved {agent_type} stats to {STATS_D_FILENAME}") # Reduce noise
        except Exception as e:
            print(f"Error writing stats to {STATS_D_FILENAME}: {e}")
def update():
    global state, game, high_score, active_agent, q_agent, dqn_agent, epoch_count
    
    # --- Handle Global Inputs (Mute, Speed) ---
    if key_just_pressed(pygame.K_m): # Mute toggle
        if game:
            game.muted = not game.muted
            print(f"Sounds Muted: {game.muted}")
            if game.muted: game.stop_looped_sounds()

    if key_just_pressed(pygame.K_EQUALS): # Increase speed
        if game:
            game.speed_multiplier = min(MAX_SPEED_MULTIPLIER, game.speed_multiplier + 50)
            print(f"Game Speed: {game.speed_multiplier}x")

    if key_just_pressed(pygame.K_MINUS): # Decrease speed
         if game:
            game.speed_multiplier = max(1, game.speed_multiplier - 10)
            print(f"Game Speed: {game.speed_multiplier}x")

    # --- State-specific updates and mode switching ---

    if state == State.MENU:
        # Handle STARTING keys from Menu
        if key_just_pressed(pygame.K_SPACE): # Start MANUAL
            reset_all_random_generators()
            state = State.MANUAL
            active_agent = None
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = None # No agent in manual
            print("Starting MANUAL mode")
            
        elif key_just_pressed(pygame.K_a):
            state = State.AUTO
            active_agent = None
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = None # No agent in manual
            print("Starting AUTO mode (algorithm based)")

        elif key_just_pressed(pygame.K_q): # Start AUTO_QLEARN
            reset_all_random_generators()
            state = State.AUTO_QLEARN
            active_agent = q_agent
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = active_agent
            if game.bunner: game.bunner.last_state_for_learning = None
            print("Starting AUTO mode (Q-Learning)")
            
        elif key_just_pressed(pygame.K_n): # Start AUTO_DQN
            reset_all_random_generators()
            state = State.AUTO_DQN
            active_agent = dqn_agent
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = active_agent
            if game.bunner: game.bunner.last_state_for_learning = None
            print("Starting AUTO mode (DQN)")
        else:
            # Update menu animation only if no mode start key was pressed
            if game: game.update() # Update menu animation

    elif state == State.MANUAL or state == State.AUTO_QLEARN or state == State.AUTO_DQN or state == State.AUTO:
        # Handle SWITCHING keys during gameplay
        if key_just_pressed(pygame.K_p): # Switch to MANUAL mode
            if state != State.MANUAL:
                state = State.MANUAL
                active_agent = None # No agent active in manual mode
                if game: game.agent = None # Detach agent from game
                print("Switched to MANUAL mode")
            # else: print("Already in MANUAL mode.") # Optional: feedback if already in mode

        if key_just_pressed(pygame.K_q): # Switch to AUTO_QLEARN mode
            if state != State.AUTO_QLEARN:
                state = State.AUTO_QLEARN
                active_agent = q_agent # Set active agent
                if game:
                    game.agent = active_agent # Attach agent to game
                    # Reset learning state if switching mid-game
                    if game.bunner:
                        game.bunner.last_state_for_learning = None
                        game.bunner.last_action_for_learning = None
                print("Switched to AUTO mode (Q-Learning)")
            # else: print("Already in AUTO mode (Q-Learning).") # Optional: feedback

        if key_just_pressed(pygame.K_n): # Switch to AUTO_DQN mode
            if state != State.AUTO_DQN:
                state = State.AUTO_DQN
                active_agent = dqn_agent # Set active agent
                if game:
                    game.agent = active_agent # Attach agent to game
                     # Reset learning state if switching mid-game
                    if game.bunner:
                        game.bunner.last_state_for_learning = None
                        game.bunner.last_action_for_learning = None
                print("Switched to AUTO mode (DQN)")
            # else: print("Already in AUTO mode (DQN).") # Optional: feedback
        
        if key_just_pressed(pygame.K_a):
            if state != State.AUTO:
                state = State.AUTO
                active_agent = None
                if game: game.agent = None
                print("Switched to AUTO mode (algorithm based)")

        # --- Game Logic (Update, Game Over Check) ---
        # Ensure game and bunner exist before proceeding
        if game and game.bunner:
            if game.bunner.state != PlayerState.ALIVE and game.bunner.timer <= 0:
                # Game Over logic
                current_score = game.score()
                high_score = max(high_score, current_score)
                try:
                    with open("high1.txt", "w") as file: file.write(str(high_score))
                except: pass # Ignore write errors

                # If an agent was active, update its stats
                if active_agent:
                    active_agent.update_stats(current_score, is_death=True)

                    # Decay epsilon only for the active agent at the end of an episode
                    if hasattr(active_agent, 'epsilon') and hasattr(active_agent, 'epsilon_min') and hasattr(active_agent, 'epsilon_decay'):
                        if active_agent.epsilon > active_agent.epsilon_min:
                            active_agent.epsilon *= active_agent.epsilon_decay
                            # print(f"Decayed {type(active_agent).__name__} epsilon to: {active_agent.epsilon:.5f}") # Reduce noise

                print(f"Game Over! Score: {current_score}, High Score: {high_score}. Agent: {type(active_agent).__name__ if active_agent else 'Manual'}")

                # Increment epoch counter
                epoch_count += 1

                # Save stats periodically
                if epoch_count % STATS_SAVE_INTERVAL == 0:
                    save_stats_to_csv() # Saves stats for the agent active during this epoch

                # Store current speed and remember the mode we were in
                current_speed = game.speed_multiplier if game else 1
                previous_state = state # Remember the mode (MANUAL, AUTO_Q, AUTO_N)

                game.stop_looped_sounds()
                reset_all_random_generators() # Reset for next game

                # Restart game, potentially in the same mode
                game = Game(Bunner((WIDTH // 2, -320)))
                game.speed_multiplier = current_speed # Restore speed

                # Decide how to restart: always auto, or previous mode? Let's restart in previous auto mode.
                if previous_state == State.AUTO_QLEARN:
                    print("Restarting game in AUTO mode (Q-Learning)...")
                    state = State.AUTO_QLEARN
                    active_agent = q_agent
                elif previous_state == State.AUTO_DQN:
                    print("Restarting game in AUTO mode (DQN)...")
                    state = State.AUTO_DQN
                    active_agent = dqn_agent
                elif previous_state == State.AUTO:
                    print("Restarting game in AUTO mode (algorithm based)...")
                    state = State.AUTO
                    active_agent = None
                else: # If game ended in MANUAL, restart in MANUAL
                    print("Restarting game in MANUAL mode...")
                    state = State.MANUAL
                    active_agent = None

                game.agent = active_agent # Assign the correct agent (or None)
                if game.bunner: game.bunner.last_state_for_learning = None # Reset learning state

            else:
                # Run game updates based on speed multiplier
                updates_per_frame = game.speed_multiplier if game else 1
                for _ in range(updates_per_frame):
                    if game and (game.bunner.state == PlayerState.ALIVE or game.bunner.timer > 0):
                         game.update() # game.update() should handle calling the attached game.agent
                    else:
                        break # Don't keep updating if game ended
        elif game is None:
             print("Error: Game object is None in active game state. Returning to Menu.")
             state = State.MENU # Fallback to menu if game is unexpectedly None
        # else: # game exists but game.bunner is None. This case should ideally not be reached if state is MANUAL/AUTO_Q/AUTO_DQN.
             # print("Error: game.bunner is None in active game state. Returning to Menu.")
             # state = State.MENU # Fallback

    elif state == State.GAME_OVER: # Should not be reached if we auto-restart
        if key_just_pressed(pygame.K_SPACE):
            game.stop_looped_sounds()
            state = State.MENU
            active_agent = None
            game = Game() # New game for menu

def draw():
    screen.clear()
    if game: game.draw()

    if state == State.MENU:
        screen.blit("title", (0, 0))
        start_frame = [0, 1, 2, 1][(game.scroll_pos // 6 % 4)] if game else 0
        screen.blit("start" + str(start_frame), ((WIDTH - 270) // 2, HEIGHT - 240))
        # Update menu text
        screen.draw.text("PRESS Q FOR Q-LEARN AUTO", ((WIDTH - 290) // 2, HEIGHT - 170))
        screen.draw.text("PRESS N FOR DQN AUTO", ((WIDTH - 250) // 2, HEIGHT - 140))
        screen.draw.text("PRESS A FOR AUTO", ((WIDTH - 250) // 2, HEIGHT - 200))
        screen.draw.text("PRESS SPACE FOR MANUAL", ((WIDTH - 250) // 2, HEIGHT - 110))
        screen.draw.text("M: Mute | +/-: Speed | P: Manual", (10, HEIGHT - 30), fontsize=20, color="yellow")

    elif state == State.MANUAL or state == State.AUTO_QLEARN or state == State.AUTO_DQN:
        display_number(screen, game.score(), 0, 0, 0)
        display_number(screen, high_score, 1, WIDTH - 10, 1)
        
        # Display current mode and speed
        mode_text = "MANUAL" if state == State.MANUAL else "AUTO Q-LEARN" if state == State.AUTO_QLEARN else "AUTO DQN" if state == State.AUTO_DQN else "AUTO MODE"
        speed_text = f"{game.speed_multiplier}x" if game else "1x"
        mute_text = "MUTED" if game and game.muted else ""
        status_line = f"Mode: {mode_text} | Speed: {speed_text} {mute_text}"
        screen.draw.text(status_line, (10, HEIGHT - 30), fontsize=20, color="yellow")
        
        # Display active agent stats if in an auto mode
        if active_agent and game and game.bunner:
            agent_type_str = type(active_agent).__name__
            y_offset = 55 # Start lower to accommodate mode line
            text_color = "cyan" if agent_type_str == "DQNAgent" else "lightgreen" # Different colors
            
            # Common stats (ensure attributes exist)
            agent_epsilon = getattr(active_agent, 'epsilon', 'N/A')
            agent_best_score = getattr(active_agent, 'best_score', 'N/A')
            agent_avg_score = getattr(active_agent, 'avg_score', 0) # Default to 0 if not present
            agent_deaths = getattr(active_agent, 'total_deaths', 'N/A')
            agent_best_epoch = getattr(active_agent, 'best_epoch', 'N/A')
            
            # Agent-specific stats
            if isinstance(active_agent, QLearningAgent):
                states_or_steps_label = "States Learned"
                states_or_steps_value = len(active_agent.q_table)
            elif isinstance(active_agent, DQNAgent):
                states_or_steps_label = "Learn Steps"
                states_or_steps_value = getattr(active_agent, 'steps_done', 'N/A')
            else:
                 states_or_steps_label = "N/A"
                 states_or_steps_value = "N/A"
                 
            # Action display (assuming bunner stores it)
            q_action = getattr(game.bunner, 'current_action_str', 'N/A') 

            screen.draw.text(f"Epoch: {epoch_count}", (WIDTH - 140, HEIGHT - 30), fontsize=20, color="yellow") # Keep epoch top right
            screen.draw.text(f"Agent: {agent_type_str}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"Epsilon: {agent_epsilon:.4f}" if isinstance(agent_epsilon, float) else f"Epsilon: {agent_epsilon}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"{states_or_steps_label}: {states_or_steps_value}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"Action: {q_action}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            # Q-value range might be harder to get generically for DQN, skip for now
            screen.draw.text(f"Current Score: {game.score()}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"Best Score: {agent_best_score} (Ep {agent_best_epoch})", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"Avg Score (Last 100): {agent_avg_score:.1f}" if isinstance(agent_avg_score, float) else f"Avg Score: {agent_avg_score}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            screen.draw.text(f"Total Deaths: {agent_deaths}", (10, HEIGHT - y_offset), fontsize=18, color=text_color); y_offset += 22
            
    elif state == State.GAME_OVER: # Should not be reached
        screen.blit("gameover", (0, 0))
        if game: 
            final_score = game.score() 
            screen.draw.text(f"FINAL SCORE: {final_score}", center=(WIDTH // 2, HEIGHT // 2 + 50), fontsize=40, color="white")
        screen.draw.text("PRESS SPACE TO RETURN TO MENU", center=(WIDTH // 2, HEIGHT // 2 + 100), fontsize=30, color="white")

# Set up sound system
try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(16)
except: pass

# Initialize agents, stats file, and load high score
initialize_agents() # Init both agents
initialize_stats_file() 
load_high_score()
state = State.MENU
active_agent = None # Start with no active agent

# Reset random generators for the initial game menu
reset_all_random_generators()
game = Game() # Start with a game instance for the menu animations

# Start the game
print("Starting game...")
pgzrun.go() 
