import pgzero, pgzrun, pygame, sys, atexit
from enum import Enum

# Import our modules
from utils import check_python_version, key_just_pressed, display_number, init_random_seeds
from constants import (WIDTH, HEIGHT, TITLE, DIRECTION_UP, DIRECTION_RIGHT, 
                       DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT, RANDOM_SEED)
from states import State, PlayerState
from game import Game
from player import Bunner
from q_learning import QLearningAgent # Import the agent
from rows import reset_random_generator as reset_rows_random
from actors import reset_random_generator as reset_actors_random

# Function to reset all random generators
def reset_all_random_generators():
    """Reset all random generators across all modules to ensure consistent starting state"""
    init_random_seeds(RANDOM_SEED)
    reset_rows_random()
    reset_actors_random()
    print("All random generators have been reset to ensure deterministic behavior")

# Check versions before continuing
check_python_version()

# Initialize random seeds for deterministic environment
reset_all_random_generators()

# Global game state
state = State.MENU
high_score = 0
game = None
agent = None # Global agent instance
epoch_count = 0 # Track number of games played/restarts

# Define all possible actions for the agent
ALL_ACTIONS = [DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_WAIT]

MAX_SPEED_MULTIPLIER = 20
TARGET_FPS = 60 # Base FPS

def load_high_score():
    global high_score
    try:
        with open("high1.txt", "r") as f:
            high_score = int(f.read())
    except:
        # If opening the file fails (likely because it hasn't yet been created), set high score to 0
        high_score = 0

def initialize_agent():
    """Initializes the Q-learning agent and loads its table."""
    global agent
    agent = QLearningAgent(actions=ALL_ACTIONS)
    # agent.load_q_table() # Loading handled within QLearningAgent constructor
    print("Q-Learning agent initialized.")

def save_agent_table():
    """Saves the Q-learning agent's table if the agent exists."""
    if agent:
        print("Attempting to save Q-table...")
        agent.save_q_table()
    else:
        print("No agent found, skipping Q-table save.")

# Register the save function to be called on exit
atexit.register(save_agent_table)

def update():
    global state, game, high_score, agent, epoch_count
    
    # Handle global inputs (mute, speed, mode switch)
    if key_just_pressed(pygame.K_m): # Mute toggle
        if game:
            game.muted = not game.muted
            print(f"Sounds Muted: {game.muted}")
            if game.muted:
                 game.stop_looped_sounds() # Stop loops immediately when muted
            # Looped sounds will restart automatically if unmuted and volume > 0

    if key_just_pressed(pygame.K_EQUALS): # Increase speed (using EQUALS for +)
        if game:
            game.speed_multiplier = min(MAX_SPEED_MULTIPLIER, game.speed_multiplier + 1)
            print(f"Game Speed: {game.speed_multiplier}x")

    if key_just_pressed(pygame.K_MINUS): # Decrease speed
         if game:
            game.speed_multiplier = max(1, game.speed_multiplier - 1)
            print(f"Game Speed: {game.speed_multiplier}x")

    if key_just_pressed(pygame.K_p): # Switch between AUTO and MANUAL
        if state == State.AUTO:
            state = State.MANUAL
            print("Switched to MANUAL mode")
        elif state == State.MANUAL:
            state = State.AUTO
            print("Switched to AUTO mode")
            # Ensure agent is ready if switching to AUTO mid-game
            if game and game.bunner:
                game.bunner.last_state_for_learning = None # Reset learning state
                game.bunner.last_action_for_learning = None
    
    # State-specific updates
    if state == State.MENU:
        if key_just_pressed(pygame.K_SPACE):
            # Reset random generators for deterministic start
            reset_all_random_generators()
            state = State.MANUAL
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = agent # Attach agent even for manual start?
        elif key_just_pressed(pygame.K_a): # Start in Auto mode
            # Reset random generators for deterministic start
            reset_all_random_generators()
            state = State.AUTO
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = agent # Attach agent to the game
            # Reset player's learning state at start of auto game
            game.bunner.last_state_for_learning = None
            game.bunner.last_action_for_learning = None
        else:
            # Update menu animation even if no key pressed
            if game: game.update()

    elif state == State.MANUAL or state == State.AUTO:
        if game.bunner.state != PlayerState.ALIVE and game.bunner.timer <= 0:
            # Game Over logic
            current_score = game.score()
            high_score = max(high_score, current_score)
            try:
                with open("high1.txt", "w") as file:
                    file.write(str(high_score))
            except:
                # If an error occurs writing the file, just ignore it and carry on, rather than crashing
                pass

            # Update agent statistics
            if state == State.AUTO and game.agent:
                game.agent.update_stats(current_score, is_death=True)

            print(f"Game Over! Score: {current_score}, High Score: {high_score}")
            # Optionally save Q-table upon game over
            # save_agent_table()

            # Reset for next game (or menu)
            # state = State.GAME_OVER # Go to game over screen
            # Instead of Game Over screen, let's restart automatically in AUTO mode for training
            print("Restarting game in AUTO mode...")
            epoch_count += 1 # Increment epoch counter
            # Store current speed before resetting game
            current_speed = game.speed_multiplier if game else 1
            
            game.stop_looped_sounds()
            
            # Reset random generators for deterministic start
            reset_all_random_generators()
            
            game = Game(Bunner((WIDTH // 2, -320)))
            game.agent = agent # Re-attach agent
            game.speed_multiplier = current_speed # Restore previous speed
            game.bunner.last_state_for_learning = None # Reset learning state
            game.bunner.last_action_for_learning = None
            state = State.AUTO # Start next game in AUTO
            
        else:
            # Run game updates based on speed multiplier
            # Simple approach: call update multiple times per frame
            # More robust: adjust movement/timing within update based on multiplier (harder)
            updates_per_frame = game.speed_multiplier if game else 1
            for _ in range(updates_per_frame):
                if game and (game.bunner.state == PlayerState.ALIVE or game.bunner.timer > 0):
                     game.update()
                else:
                    break # Don't keep updating if game ended mid-multiplier loop

    elif state == State.GAME_OVER: # This state might not be reached if we auto-restart
        if key_just_pressed(pygame.K_SPACE):
            game.stop_looped_sounds()
            state = State.MENU
            game = Game() # New game, no player, no agent attached yet

def draw():
    # Clear screen (important for higher speeds)
    screen.clear()
    
    if game: # Ensure game exists before drawing
        game.draw()

    if state == State.MENU:
        screen.blit("title", (0, 0))
        start_frame = [0, 1, 2, 1][(game.scroll_pos // 6 % 4)] if game else 0
        screen.blit("start" + str(start_frame), ((WIDTH - 270) // 2, HEIGHT - 240))
        screen.draw.text("PRESS A FOR AUTO MODE", ((WIDTH - 225) // 2, HEIGHT - 170))
        screen.draw.text("PRESS SPACE FOR MANUAL", ((WIDTH - 250) // 2, HEIGHT - 140))
        screen.draw.text("M: Mute | +/-: Speed | P: Toggle Mode", (10, HEIGHT - 30), fontsize=20, color="yellow")

    elif state == State.MANUAL or state == State.AUTO:
        display_number(screen, game.score(), 0, 0, 0)
        display_number(screen, high_score, 1, WIDTH - 10, 1)
        # Display current mode and speed
        mode_text = "MANUAL" if state == State.MANUAL else "AUTO"
        speed_text = f"{game.speed_multiplier}x" if game else "1x"
        mute_text = "MUTED" if game and game.muted else ""
        status_line = f"Mode: {mode_text} | Speed: {speed_text} {mute_text}"
        screen.draw.text(status_line, (10, HEIGHT - 30), fontsize=20, color="yellow")
        
        # Display Q-learning stats if in AUTO mode and agent exists
        if state == State.AUTO and game and game.agent and game.bunner:
            # Basic stats
            q_epsilon = game.agent.epsilon
            q_states = len(game.agent.q_table)
            q_action = game.bunner.current_action_str
            
            # Enhanced stats
            total_steps = epoch_count * 500  # Estimate, could track more accurately
            avg_steps_per_epoch = 0
            max_q_value = 0
            min_q_value = 0
            
            # Calculate more advanced stats
            if q_states > 0:
                # Find max and min Q-values in the table
                all_q_values = []
                for state_values in game.agent.q_table.values():
                    all_q_values.extend(state_values.values())
                if all_q_values:
                    max_q_value = max(all_q_values)
                    min_q_value = min(all_q_values)
                
                # Calculate average steps per epoch
                if epoch_count > 0:
                    avg_steps_per_epoch = total_steps / epoch_count
            
            # Get current score as a performance metric
            current_score = game.score()
            
            # Display advanced stats
            y_offset = 30
            text_color = "cyan"
            screen.draw.text(f"Epoch: {epoch_count}", (WIDTH - 140, HEIGHT - y_offset), fontsize=20, color="yellow")
            y_offset += 25
            screen.draw.text(f"Epsilon: {q_epsilon:.4f}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
            y_offset += 25
            screen.draw.text(f"States Learned: {q_states}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
            y_offset += 25
            screen.draw.text(f"Action: {q_action}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
            y_offset += 25
            screen.draw.text(f"Q-value range: [{min_q_value:.1f}, {max_q_value:.1f}]", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
            y_offset += 25
            screen.draw.text(f"Current Score: {current_score}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
            
            # Show additional stats from agent
            if hasattr(game.agent, 'best_score'):
                y_offset += 25
                screen.draw.text(f"Best Score: {game.agent.best_score}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
                
                if hasattr(game.agent, 'total_deaths'):
                    y_offset += 25
                    screen.draw.text(f"Total Deaths: {game.agent.total_deaths}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
                
                if hasattr(game.agent, 'avg_score'):
                    y_offset += 25
                    screen.draw.text(f"Avg Score: {game.agent.avg_score:.1f}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)
                    
                if hasattr(game.agent, 'best_epoch'):
                    y_offset += 25
                    screen.draw.text(f"Best Run: Epoch {game.agent.best_epoch}", (10, HEIGHT - y_offset), fontsize=18, color=text_color)

    elif state == State.GAME_OVER:
        screen.blit("gameover", (0, 0))
        # Add text to show score and prompt restart/menu
        if game: 
            final_score = game.score() # May need to store score before game reset
            screen.draw.text(f"FINAL SCORE: {final_score}", center=(WIDTH // 2, HEIGHT // 2 + 50), fontsize=40, color="white")
        screen.draw.text("PRESS SPACE TO RETURN TO MENU", center=(WIDTH // 2, HEIGHT // 2 + 100), fontsize=30, color="white")

# Set up sound system
try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(16)
except:
    # If an error occurs, just ignore it
    pass

# Initialize agent and load high score
initialize_agent() 
load_high_score()
state = State.MENU

# Reset random generators for the initial game
reset_all_random_generators()
game = Game() # Start with a game instance for the menu animations

# Start the game
pgzrun.go() 
