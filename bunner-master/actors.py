from pgzero.actor import Actor
import random
from constants import WIDTH, RANDOM_SEED

# Create a deterministic random generator if a seed is provided
rand_generator = random.Random(RANDOM_SEED)

# Function to reset the random generator state
def reset_random_generator():
    global rand_generator
    rand_generator = random.Random(RANDOM_SEED)
    return rand_generator

class MyActor(Actor):
    def __init__(self, image, pos, anchor=("center", "bottom")):
        super().__init__(image, pos, anchor)
        self.children = []
        # Use the global generator (which may have been reset by Game.__init__)
        self.rand = rand_generator

    def draw(self, offset_x, offset_y):
        self.x += offset_x
        self.y += offset_y

        super().draw()
        for child_obj in self.children:
            child_obj.draw(self.x, self.y)

        self.x -= offset_x
        self.y -= offset_y

    def update(self):
        for child_obj in self.children:
            child_obj.update()

class Eagle(MyActor):
    def __init__(self, pos):
        super().__init__("eagles", pos)
        self.children.append(MyActor("eagle", (0, -32)))
        self.base_speed = 12  # Store the base speed

    def update(self):
        # Import game here to avoid circular imports
        from game import game
        
        # Get speed multiplier for eagle movement
        speed_multiplier = game.speed_multiplier if hasattr(game, 'speed_multiplier') else 1
        
        # Apply speed multiplier to eagle movement
        actual_speed = self.base_speed * speed_multiplier
        self.y += actual_speed

class Mover(MyActor):
    def __init__(self, dx, image, pos):
        super().__init__(image, pos)
        self.dx = dx
        self.base_dx = dx  # Store the original dx value

    def update(self):
        # Note: The game.py update already temporarily modifies dx for all objects
        # This is a backup in case any Mover objects are updated outside of game.update
        from game import game
        
        # Get the speed multiplier if available
        speed_multiplier = game.speed_multiplier if hasattr(game, 'speed_multiplier') else 1
        
        # Use base_dx to calculate the current frame's movement
        # This avoids compounding the multiplier effect if update is called multiple times
        actual_dx = self.base_dx * speed_multiplier
        
        self.x += actual_dx

class Car(Mover):
    SOUND_ZOOM = 0
    SOUND_HONK = 1

    def __init__(self, dx, pos):
        image = "car" + str(rand_generator.randint(0, 3)) + ("0" if dx < 0 else "1")
        super().__init__(dx, image, pos)
        self.played = [False, False]
        self.sounds = [("zoom", 2), ("honk", 1.5)]

    def play_sound(self, num):
        if not self.played[num]:
            from game import game
            game.play_sound(*self.sounds[num])
            self.played[num] = True

class Log(Mover):
    def __init__(self, dx, pos):
        image = "log" + str(rand_generator.randint(0, 1))
        super().__init__(dx, image, pos)

class Train(Mover):
    def __init__(self, dx, pos):
        image = "train" + str(rand_generator.randint(0, 2)) + ("0" if dx < 0 else "1")
        super().__init__(dx, image, pos)

class Hedge(MyActor):
    def __init__(self, x, y, pos):
        super().__init__("bush"+str(x)+str(y), pos) 
