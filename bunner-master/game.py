import pygame
import random
from actors import Eagle
from constants import HEIGHT, ROW_HEIGHT, RANDOM_SEED
from rows import Grass, Road, Row

# Create a deterministic random generator if a seed is provided
rand_generator = random.Random(RANDOM_SEED)

# Global variable to store the game instance for modules that need to access it
game = None

class Game:
    def __init__(self, bunner=None):
        global game
        game = self  # Set the global game reference
        
        # Reset the random generator state to ensure consistent starting layout
        # This ensures each new game starts with the same road pattern
        global rand_generator
        rand_generator = random.Random(RANDOM_SEED)
        
        self.bunner = bunner
        self.looped_sounds = {}
        self.muted = False # Sound mute state
        self.speed_multiplier = 1 # Game speed multiplier (1x, 2x, ..., 20x)
        self.agent = None # Placeholder for Q-learning agent
        self.actors = [] # List to hold non-row, non-player actors (e.g., effects)
        
        # Store a reference to the random generator
        self.rand = rand_generator

        try:
            if bunner:
                music.set_volume(0.4)
            else:
                music.play("result")
                music.set_volume(0.4)
        except:
            pass

        self.eagle = None
        self.frame = 0

        # Always start with the same initial row
        self.rows = [Grass(None, 0, 0)]
        self.scroll_pos = -HEIGHT

    def update(self):
        if self.bunner:
            self.scroll_pos -= max(1, min(20, float(self.scroll_pos + HEIGHT - self.bunner.y) / (HEIGHT // 4)))
        else:
            self.scroll_pos -= 1

        self.rows = [row for row in self.rows if row.y < int(self.scroll_pos) + HEIGHT + ROW_HEIGHT * 2]

        while self.rows[-1].y > int(self.scroll_pos)+ROW_HEIGHT:
            new_row = self.rows[-1].next()
            self.rows.append(new_row)

        # Update all relevant game objects
        update_list = self.rows + self.actors # Combine rows and general actors
        if self.bunner: update_list.append(self.bunner)
        if self.eagle: update_list.append(self.eagle)

        for obj in update_list:
            if obj:
                obj.update()

        # Simple cleanup for actors without sophisticated lifecycle (e.g., remove splat after time?)
        # For now, actors list might grow indefinitely. Needs enhancement later.
        # self.actors = [actor for actor in self.actors if actor.is_alive()] # Example cleanup

        if self.bunner:
            for name, count, row_class in [("traffic", 3, Road)]:
                volume = sum([16.0 / max(16.0, abs(r.y - self.bunner.y)) for r in self.rows if isinstance(r, row_class)]) - 0.2
                volume = min(0.4, volume)
                self.loop_sound(name, count, volume)

        return self

    def draw(self):
        from constants import DEBUG_SHOW_ROW_BOUNDARIES, ROW_HEIGHT
        
        # Combine all drawable objects
        all_objs = list(self.rows) + list(self.actors) # Start with rows and general actors

        if self.bunner:
            all_objs.append(self.bunner)

        def sort_key(obj):
            # Handle potential missing y attribute gracefully for sorting?
            y_pos = getattr(obj, 'y', -float('inf')) # Default to very top if no y
            return (y_pos + 39) // ROW_HEIGHT

        all_objs.sort(key=sort_key)
        
        # Draw eagle last (on top)
        if self.eagle:
            all_objs.append(self.eagle)
        
        for obj in all_objs:
            if obj:
                obj.draw(0, -int(self.scroll_pos))

        if DEBUG_SHOW_ROW_BOUNDARIES:
            for obj in all_objs:
                if obj and isinstance(obj, Row):
                    pygame.draw.rect(screen.surface, (255, 255, 255), pygame.Rect(obj.x, obj.y - int(self.scroll_pos), screen.surface.get_width(), ROW_HEIGHT), 1)
                    screen.draw.text(str(obj.index), (obj.x, obj.y - int(self.scroll_pos) - ROW_HEIGHT))

    def score(self):
        score_val = int(-320 - self.bunner.min_y) // 40
        try:
            with open("score1.txt", "w") as file:
                file.write(str(score_val))
        except:
            pass
        return score_val

    def play_sound(self, name, count=1):
        # Only play sound if not muted
        if not self.muted:
            try:
                # Use our deterministic random generator
                full_name = name + str(self.rand.randint(0, count - 1))
                sound = getattr(sounds, full_name) 
                sound.play()
            except Exception as e:
                # print(f"Error playing sound {name}: {e}")
                pass # Gracefully handle missing sounds or errors
        
    def loop_sound(self, name, count, volume):
        # Respect mute for looped sounds as well
        try:
            if volume > 0 and not name in self.looped_sounds:
                # Only start loop if not muted
                if not self.muted:
                    # Use our deterministic random generator
                    full_name = name + str(self.rand.randint(0, count - 1))
                    sound = getattr(sounds, full_name)
                    sound.play(-1)  # -1 means sound will loop indefinitely
                    self.looped_sounds[name] = sound
                else:
                    # If muted, ensure it doesn't start playing if it wasn't already
                    return 

            if name in self.looped_sounds:
                sound = self.looped_sounds[name]
                # If muted, set volume to 0 and keep reference, otherwise use calculated volume
                effective_volume = 0 if self.muted else volume 
                
                if effective_volume > 0:
                    sound.set_volume(effective_volume)
                else:
                    # Stop sound if volume is 0 or muted state requires stopping
                    sound.stop()
                    del self.looped_sounds[name]
        except Exception as e:
            # print(f"Error looping sound {name}: {e}")
            pass

    def stop_looped_sounds(self):
        try:
            for sound in self.looped_sounds.values():
                sound.stop()
            self.looped_sounds.clear()
        except:
            pass 
