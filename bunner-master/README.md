# Task

Add auto mode for the game in which, the algoritm determines in which direction the bunny needs to go using different game conditions and cases.

# Until saturday

1. Copy the code from the book for bunner.
2. Describe every class and function in the code and be able to explain their content.
3. At most one car on a row at a time.
4. 1# At most one log.
   2# Or remove logs and water.
5. Implement obstacale avoiding metod.

# New task

1. Polish the ai_decide function.
2. Remove all comented code.
3. Optional: Add the train method.

# Leetcode challenges

1. https://leetcode.com/problems/two-sum/description/ Complete the task with brute force then use dictionary.

# Until next weekend

1. Reduce road number to maximum 2.
2. Upgrade road logic to ensure bunner never dies .
3. Upgrade train avoidance logic to wait for train arrival.
4. Every time bunner dies save number of steps and number of iteration to txt file.

---

# Bunner Game - Refactored

This is a refactored version of the Bunner game. The original code has been split into multiple modules for better organization and maintainability.

## File Structure

-   `main.py` - Entry point that initializes the game and runs it
-   `constants.py` - Game constants and configuration
-   `utils.py` - Utility functions
-   `actors.py` - Base actor classes and simple actors
-   `player.py` - Bunner class and player-related functionality
-   `rows.py` - Row classes and their implementations
-   `game.py` - Game class implementation
-   `states.py` - Game state enumerations

## How to Run

The game can be run using Pygame Zero:

```
pgzrun main.py
```

## Game Controls

-   Press SPACE to start the game in manual mode
-   Press A to start the game in auto mode
-   Use arrow keys to control the bunny in manual mode

## Refactoring Notes

The original `bunner.py` file was refactored into multiple modules to:

1. Separate concerns into logical components
2. Make the code more modular and maintainable
3. Reduce file sizes for easier navigation
4. Enable better code reuse

Circular imports were handled by using strategic import statements within functions where necessary.
