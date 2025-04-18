import random
from actors import MyActor, Car, Train, Hedge
from constants import ROW_HEIGHT, WIDTH, RANDOM_SEED
from states import PlayerState

# Create a deterministic random generator if a seed is provided
rand_generator = random.Random(RANDOM_SEED)

# Function to reset the random generator state
def reset_random_generator():
    global rand_generator
    rand_generator = random.Random(RANDOM_SEED)
    return rand_generator

class Row(MyActor):
    def __init__(self, base_image, index, y):
        super().__init__(base_image + str(index), (0, y), ("left", "bottom"))
        self.index = index
        self.dx = 0
        # Use the global generator (which may have been reset by Game.__init__)
        self.rand = rand_generator

    def next(self):
        return

    def collide(self, x, margin=0):
        for child_obj in self.children:
            if x >= child_obj.x - (child_obj.width / 2) - margin and x < child_obj.x + (child_obj.width / 2) + margin:
                return child_obj
        return None

    def push(self):
        return 0

    def check_collision(self, x):
        return PlayerState.ALIVE, 0

    def allow_movement(self, x):
        return x >= 16 and x <= WIDTH-16

    def play_sound(self):
        pass

class ActiveRow(Row):
    def __init__(self, child_type, dxs, base_image, index, y, maxchildren=None):
        super().__init__(base_image, index, y)
        self.child_type = child_type    
        self.timer = 0
        self.maxchildren = maxchildren
        self.dx = self.rand.choice(dxs)   

        x = -WIDTH / 2 - 70
        counter = maxchildren
        
        while x < WIDTH / 2 + 70 and counter != 0:
            x += self.rand.randint(240, 480)
            pos = (WIDTH / 2 + (x if self.dx > 0 else -x), 0)
            self.children.append(self.child_type(self.dx, pos))
            counter -= 1
    
    def update(self):
        super().update()
        # Import game here to avoid circular imports
        from game import game
        
        # Get speed multiplier for timer adjustment
        speed_multiplier = game.speed_multiplier if hasattr(game, 'speed_multiplier') else 1
        
        self.children = [c for c in self.children if c.x > -70 and c.x < WIDTH + 70]
        # Apply speed multiplier to timer reduction
        timer_reduction = min(abs(self.timer), speed_multiplier) if self.timer < 0 else speed_multiplier
        self.timer -= timer_reduction

        if self.timer < -100:
            pos = (WIDTH + 70 if self.dx < 0 else -70, 0)
            self.children.append(self.child_type(self.dx, pos))
            # Adjust spawn timer based on speed - faster speed means quicker spawning
            self.timer = (1 + self.rand.random()) * (240 / abs(self.dx)) / speed_multiplier

class Grass(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("grass", index, y)

    def allow_movement(self, x):
        return super().allow_movement(x) and not self.collide(x, 8)

    def play_sound(self):
        from game import game
        game.play_sound("grass", 1)

    def next(self):
        if self.index <= 5:
            row_class, index = Grass, self.index + 8
        elif self.index == 6:
            row_class, index = Grass, 7
        elif self.index == 7:
            row_class, index = Grass, 15
        elif self.index >= 8 and self.index <= 14:
            row_class, index = Grass, self.index + 1
        else:
            row_class, index = self.rand.choice((Road, )), 0
        
        return row_class(self, index, self.y - ROW_HEIGHT)

class Dirt(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("dirt", index, y)

    def play_sound(self):
        from game import game
        game.play_sound("dirt", 1)

    def next(self):
        if self.index <= 5:
            row_class, index = Dirt, self.index + 8
        elif self.index == 6:
            row_class, index = Dirt, 7
        elif self.index == 7:
            row_class, index = Dirt, 15
        elif self.index >= 8 and self.index <= 14:
            row_class, index = Dirt, self.index + 1
        else:
            row_class, index = self.rand.choice((Road, )), 0 

        return row_class(self, index, self.y - ROW_HEIGHT)

class Road(ActiveRow):
    def __init__(self, predecessor, index, y):
        # Specify the possible directions and speeds from which the movement of cars on this row will be chosen
        # We use Python's set data structure to specify that the car velocities on this row will be any of the numbers
        # from -5 to 5, except for zero or the velocity of the cars on the previous row
        dxs = list(set(range(-3, 3)) - set([0, predecessor.dx]))
        super().__init__(Car, dxs, "road", index, y, maxchildren=2)
        
    def update(self):
        super().update()
        
        # Import game here to avoid circular imports
        from game import game
        
        for y_offset, car_sound_num in [(-ROW_HEIGHT, Car.SOUND_ZOOM), (0, Car.SOUND_HONK), (ROW_HEIGHT, Car.SOUND_ZOOM)]:
            if game.bunner and game.bunner.y == self.y + y_offset:
                for child_obj in self.children:
                    if isinstance(child_obj, Car):
                        dx = child_obj.x - game.bunner.x
                        if abs(dx) < 100 and ((child_obj.dx < 0) != (dx < 0)) and (y_offset == 0 or abs(child_obj.dx) > 1):
                            child_obj.play_sound(car_sound_num)

    def check_collision(self, x):
        if self.collide(x):
            from game import game
            game.play_sound("splat", 1)
            return PlayerState.SPLAT, 0
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self):
        from game import game
        game.play_sound("road", 1)

    def next(self):
        if self.index == 0:
            row_class, index = Road, 1
        elif self.index < 2:
            r = self.rand.random()
            if r < 0.5:
                row_class, index = Road, self.index + 1
            elif r < 0.7:
                row_class, index = Grass, self.rand.randint(0,6)
            elif r < 0.4:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0
        else:
            r = self.rand.random()
            if r < 0.6:
                row_class, index = Grass, self.rand.randint(0,6)
            elif r < 0.4:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0

        return row_class(self, index, self.y - ROW_HEIGHT)

class Pavement(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("side", index, y)

    def play_sound(self):
        from game import game
        game.play_sound("sidewalk", 1)

    def next(self):
        if self.index < 2:
            row_class, index = Pavement, self.index + 1
        else:
            row_class, index = Road, 0

        return row_class(self, index, self.y - ROW_HEIGHT)

class Rail(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("rail", index, y)
        self.predecessor = predecessor
        self.train_incoming = False

    def update(self):
        super().update()

        # Import game here to avoid circular imports
        from game import game
        
        # Get speed multiplier for spawn timing adjustment
        speed_multiplier = game.speed_multiplier if hasattr(game, 'speed_multiplier') else 1
        
        if self.index == 1:
            self.children = [c for c in self.children if c.x > -1000 and c.x < WIDTH + 1000]
            
            # Increase spawn probability based on speed multiplier
            # Faster game should have more frequent train spawns
            base_spawn_probability = 0.01
            adjusted_probability = min(0.3, base_spawn_probability * speed_multiplier)
            
            if self.y < game.scroll_pos+HEIGHT and len(self.children) == 0 and self.rand.random() < adjusted_probability:
                # Train speed also affected by speed multiplier
                base_speed = self.rand.choice([-20, 20])
                train_speed = base_speed * speed_multiplier / 3  # Dividing by 3 to avoid trains moving too fast
                self.children.append(Train(train_speed, (WIDTH + 1000 if train_speed < 0 else -1000, -13)))
                game.play_sound("bell")
                self.train_incoming = True
                game.play_sound("train", 2)

    def check_collision(self, x):
        if self.index == 2 and self.predecessor.collide(x):
            from game import game
            game.play_sound("splat", 1)
            return PlayerState.SPLAT, 8    
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self):
        from game import game
        game.play_sound("grass", 1)

    def next(self):
        if self.index < 3:
            row_class, index = Rail, self.index + 1
        else:
            item = self.rand.choice(((Road, 0), ))
            row_class, index = item[0], item[1]

        return row_class(self, index, self.y - ROW_HEIGHT) 
