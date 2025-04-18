# If the window is too tall to fit on the screen, check your operating system display settings and reduce display
# scaling if it is enabled.
import pgzero.clock
import pgzero, pgzrun, pygame, sys
from random import random, randint, choice
from enum import Enum

# Check Python version number. sys.version_info gives version as a tuple, e.g. if (3,7,2,'final',0) for version 3.7.2.
# Unlike many languages, Python can compare two tuples in the same way that you can compare numbers.
if sys.version_info < (3,5):
    print("This game requires at least version 3.5 of Python. Please download it from www.python.org")
    sys.exit()

# Check Pygame Zero version. This is a bit trickier because Pygame Zero only lets us get its version number as a string.
# So we have to split the string into a list, using '.' as the character to split on. We convert each element of the
# version number into an integer - but only if the string contains numbers and nothing else, because it's possible for
# a component of the version to contain letters as well as numbers (e.g. '2.0.dev0')
# We're using a Python feature called list comprehension - this is explained in the Bubble Bobble/Cavern chapter.
pgzero_version = [int(s) if s.isnumeric() else s for s in pgzero.__version__.split('.')]
if pgzero_version < [1,2]:
    print("This game requires at least version 1.2 of Pygame Zero. You have version {0}. Please upgrade using the command 'pip3 install --upgrade pgzero'".format(pgzero.__version__))
    sys.exit()

WIDTH = 480 
HEIGHT = 800
TITLE = "Bunner Game"

ROW_HEIGHT = 40
DEBUG_SHOW_ROW_BOUNDARIES = False


class MyActor(Actor):
    def __init__(self, image, pos, anchor=("center", "bottom")):
        super().__init__(image, pos, anchor)

        self.children = []

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

    def update(self):
        self.y += 12

class PlayerState(Enum):
    ALIVE = 0
    SPLAT = 1
    SPLASH = 2
    EAGLE = 3


DIRECTION_UP = 0
DIRECTION_RIGHT = 1
DIRECTION_DOWN = 2
DIRECTION_LEFT = 3
DIRECTION_WAIT = 4

direction_keys = [keys.UP, keys.RIGHT, keys.DOWN, keys.LEFT]

# X and Y directions indexed into by in_edge and out_edge in Segment
# The indices correspond to the direction numbers above, i.e. 0 = up, 1 = right, 2 = down, 3 = left
# Numbers 0 to 3 correspond to up, right, down, left
DX = [0,4,0,-4, 0]
DY = [-4,0,4,0, 0]

class Bunner(MyActor):
    MOVE_DISTANCE = 10
    JUMP_COOLDOWN = 20


    def __init__(self, pos):
        super().__init__("blank", pos)

        self.state = PlayerState.ALIVE

        self.direction = 2
        self.timer = 0
        self.jump_cooldown = 0
        self.input_queue = []

        # Keeps track of the furthest distance we've reached so far in the level, for scoring
        # (Level Y coordinates decrease as the screen scrolls)
        self.min_y = self.y

    def handle_input(self, dir):
        # Find row that player is trying to move to. This may or may not be the row they're currently standing on,
        # depending on whether the proposed movement would take them onto a different row
        for row in game.rows:
            if row.y == self.y + Bunner.MOVE_DISTANCE * DY[dir]:
                # Found the target row
                # Can the player move to the new location? Can't move if there's something in the way
                # (or if the new location is off the screen)
                if row.allow_movement(self.x + Bunner.MOVE_DISTANCE * DX[dir]):
                    # It's okay to move here, so set direction and timer. Player will move one pixel per frame
                    # for the specified number of frames
                    self.direction = dir
                    self.timer = Bunner.MOVE_DISTANCE
                    game.play_sound("jump", 1)

                return
    
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

        if isinstance(next_row, Rail):
            if len(next_row.children) == 0:
                direction = 0
            else:
                direction = 4
                self.jump_cooldown = 10
                direction = 0
            
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
    

    def update(self):
        
        for direction in range(4):
            if key_just_pressed(direction_keys[direction]):
                self.input_queue.append(direction)
        
        
        if self.state == PlayerState.ALIVE:
            current_row = None
            next_row = None
            for index in range(len(game.rows)):
                row = game.rows[index]
                if row.y == self.y:
                    current_row = row
                    if index + 1 < len(game.rows):
                        next_row = game.rows[index + 1]
                    break

            
            if state == State.MANUAL:
            
                if self.timer == 0 and len(self.input_queue) > 0:

                    self.handle_input(self.input_queue.pop(0))
            
            if state == State.AUTO:        
                if self.timer == 0 and self.jump_cooldown == 0:
                    try:
                        dir = self._ai_decide(current_row, next_row)
                        if dir != DIRECTION_WAIT:
                            self.handle_input(dir)  
                            self.jump_cooldown = self.JUMP_COOLDOWN
                        
                    except Exception as exp:
                        print(exp)
            
            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
            
            
            land = False
            if self.timer > 0:
                # Apply movement
                self.x += DX[self.direction]
                self.y += DY[self.direction]

                self.timer -= 1
                land = self.timer == 0      # If timer reaches zero, we've just landed
                

            current_row = None
            for row in game.rows:
                if row.y == self.y:
                    current_row = row
                    break

            if current_row:
                self.state, dead_obj_y_offset = current_row.check_collision(self.x)
                if self.state == PlayerState.ALIVE:
                    self.x += current_row.push()

                    if land:
                        current_row.play_sound()
                else:
                    if self.state == PlayerState.SPLAT:
                        current_row.children.insert(0, MyActor("splat" + str(self.direction), (self.x, dead_obj_y_offset)))
                    self.timer = 100
            else:
                if self.y > game.scroll_pos + HEIGHT + 80:
                    game.eagle = Eagle((self.x, game.scroll_pos))
                    self.state = PlayerState.EAGLE
                    self.timer = 150
                    game.play_sound("eagle")

            self.x = max(16, min(WIDTH - 16, self.x))
            

        else:
            self.timer -= 1

        # Keep track of the furthest we've got in the level
        self.min_y = min(self.min_y, self.y)

        self.image = "blank"
        if self.state == PlayerState.ALIVE:
            if self.timer > 0:
                self.image = "jump" + str(self.direction)
            else:
                self.image = "sit" + str(self.direction)
        elif self.state == PlayerState.SPLASH and self.timer > 84:
            self.image = "splash" + str(int((100 - self.timer) / 2))


class Mover(MyActor):
    def __init__(self, dx, image, pos):
        super().__init__(image, pos)

        self.dx = dx

    def update(self):
        self.x += self.dx

class Car(Mover):
    SOUND_ZOOM = 0
    SOUND_HONK = 1

    def __init__(self, dx, pos):
        image = "car" + str(randint(0, 3)) + ("0" if dx < 0 else "1")
        super().__init__(dx, image, pos)


        self.played = [False, False]
        self.sounds = [("zoom", 2), ("honk", 1.5)]

    def play_sound(self, num):
        if not self.played[num]:
            game.play_sound(*self.sounds[num])
            self.played[num] = True

class Log(Mover):
    def __init__(self, dx, pos):
        image = "log" + str(randint(0, 1))
        super().__init__(dx, image, pos)

class Train(Mover):
    def __init__(self, dx, pos):
        image = "train"  +str(randint(0, 2)) + ("0" if dx < 0 else "1")
        super().__init__(dx, image, pos)


class Row(MyActor):
    def __init__(self, base_image, index, y):
        super().__init__(base_image + str(index), (0, y), ("left", "bottom"))

        self.index = index

        self.dx = 0

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

class ActiveRow(Row):
    def __init__(self, child_type, dxs, base_image, index, y, maxchildren = None):
        super().__init__(base_image, index, y)

        self.child_type = child_type    
        self.timer = 0
        self.maxchildren = maxchildren
        self.dx = choice(dxs)   

        x = -WIDTH / 2 - 70
        
        counter = maxchildren
        
        while x < WIDTH / 2 + 70 and counter != 0:
            x += randint(240, 480)
            pos = (WIDTH / 2 + (x if self.dx > 0 else -x), 0)
            self.children.append(self.child_type(self.dx, pos))
            counter -= 1
            
    
    
    def update(self):
        super().update()
        self.children = [c for c in self.children if c.x > -70 and c.x < WIDTH + 70]

        self.timer -= 1

        if self.timer < -100:
            pos = (WIDTH + 70 if self.dx < 0 else -70, 0)
            self.children.append(self.child_type(self.dx, pos))
            self.timer = (1 + random()) * (240 / abs(self.dx))

# Grass rows sometimes contain hedges
class Hedge(MyActor):
    def __init__(self, x, y, pos):
        super().__init__("bush"+str(x)+str(y), pos)


class Grass(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("grass", index, y)

    def allow_movement(self, x):
        return super().allow_movement(x) and not self.collide(x, 8)

    def play_sound(self):
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
            row_class, index = choice((Road, )), 0 # Water

        return row_class(self, index, self.y - ROW_HEIGHT)

class Dirt(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("dirt", index, y)

    def play_sound(self):
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
            row_class, index = choice((Road, )), 0 

        return row_class(self, index, self.y - ROW_HEIGHT)
    


class Road(ActiveRow):
    def __init__(self, predecessor, index, y):
        # Specify the possible directions and speeds from which the movement of cars on this row will be chosen
        # We use Python's set data structure to specify that the car velocities on this row will be any of the numbers
        # from -5 to 5, except for zero or the velocity of the cars on the previous row
        dxs = list(set(range(-3, 3)) - set([0, predecessor.dx]))
        super().__init__(Car, dxs, "road", index, y, maxchildren = 2)
        
    def update(self):
        super().update()
        for y_offset, car_sound_num in [(-ROW_HEIGHT, Car.SOUND_ZOOM), (0, Car.SOUND_HONK), (ROW_HEIGHT, Car.SOUND_ZOOM)]:
            if game.bunner and game.bunner.y == self.y + y_offset:
                for child_obj in self.children:
                    if isinstance(child_obj, Car):
                        dx = child_obj.x - game.bunner.x
                        if abs(dx) < 100 and ((child_obj.dx < 0) != (dx < 0)) and (y_offset == 0 or abs(child_obj.dx) > 1):
                            child_obj.play_sound(car_sound_num)

    def check_collision(self, x):
        if self.collide(x):
            game.play_sound("splat", 1)
            return PlayerState.SPLAT, 0
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self):
        game.play_sound("road", 1)

    def next(self):
        if self.index == 0:
            row_class, index = Road, 1
        elif self.index < 2:
            r = random()
            if r < 0.5:
                row_class, index = Road, self.index + 1
            elif r < 0.7:
                row_class, index = Grass, randint(0,6)
            elif r < 0.4:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0
        else:
            r = random()
            if r < 0.6:
                row_class, index = Grass, randint(0,6)
            elif r < 0.4:
                row_class, index = Rail, 0
            else:
                row_class, index = Pavement, 0

        return row_class(self, index, self.y - ROW_HEIGHT)

class Pavement(Row):
    def __init__(self, predecessor, index, y):
        super().__init__("side", index, y)

    def play_sound(self):
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

        if self.index == 1:
            self.children = [c for c in self.children if c.x > -1000 and c.x < WIDTH + 1000]

            
            if self.y < game.scroll_pos+HEIGHT and len(self.children) == 0 and random() < 0.01:
                dx = choice([-20, 20])
                self.children.append(Train(dx, (WIDTH + 1000 if dx < 0 else -1000, -13)))
                game.play_sound("bell")
                self.train_incoming = True
                game.play_sound("train", 2)
                   

    def check_collision(self, x):
        if self.index == 2 and self.predecessor.collide(x):
            game.play_sound("splat", 1)
            return PlayerState.SPLAT, 8    
        else:
            return PlayerState.ALIVE, 0

    def play_sound(self):
        game.play_sound("grass", 1)

    def next(self):
        if self.index < 3:
            row_class, index = Rail, self.index + 1
        else:
            item = choice( ((Road, 0), ) )
            row_class, index = item[0], item[1]


        return row_class(self, index, self.y - ROW_HEIGHT)

class Game:
    def __init__(self, bunner=None):
        self.bunner = bunner
        self.looped_sounds = {}

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


        for obj in self.rows + [self.bunner, self.eagle]:
            if obj:
                obj.update()

        if self.bunner:
            for name, count, row_class in [ ("traffic", 3, Road)]:

                volume = sum([16.0 / max(16.0, abs(r.y - self.bunner.y)) for r in self.rows if isinstance(r, row_class)]) - 0.2
                volume = min(0.4, volume)
                self.loop_sound(name, count, volume)

        return self

    def draw(self):
        all_objs = list(self.rows)

        if self.bunner:
            all_objs.append(self.bunner)

        def sort_key(obj):
            return (obj.y + 39) // ROW_HEIGHT

        all_objs.sort(key=sort_key)


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
        return int(-320 - game.bunner.min_y) // 40
        try:
            with open("score1.txt", "w") as file:
                    file.write(str(score()))
        except:
               
            pass

    def play_sound(self, name, count=1):
        
        pass
        
        
    def loop_sound(self, name, count, volume):
        try:
            # Similar to play_sound above, but for looped sounds we need to keep a reference to the sound so that we can
            # later modify its volume or turn it off. We use the dictionary self.looped_sounds for this - the sound
            # effect name is the key, and the value is the corresponding sound reference.
            if volume > 0 and not name in self.looped_sounds:
                full_name = name + str(randint(0, count - 1))
                sound = getattr(sounds, full_name)      # see play_sound method above for explanation
                sound.play(-1)  # -1 means sound will loop indefinitely
                self.looped_sounds[name] = sound

            if name in self.looped_sounds:
                sound = self.looped_sounds[name]
                if volume > 0:
                    sound.set_volume(volume)
                else:
                    sound.stop()
                    del self.looped_sounds[name]
        except:
            pass


    def stop_looped_sounds(self):
        try:
            for sound in self.looped_sounds.values():
                sound.stop()
            self.looped_sounds.clear()
        except:
            pass

key_status = {}


def key_just_pressed(key):
    result = False


    prev_status = key_status.get(key, False)


    if not prev_status and keyboard[key]:
        result = True


    key_status[key] = keyboard[key]

    return result

def display_number(n, colour, x, align):

    n = str(n)  
    for i in range(len(n)):
        screen.blit("digit" + str(colour) + n[i], (x + (i - len(n) * align) * 25, 0))


class State(Enum):
    MENU = 1
    MANUAL = 2
    GAME_OVER = 3
    AUTO = 4

def update():
    global state, game, high_score

    if state == State.MENU:
        if key_just_pressed(keys.SPACE):
            state = State.MANUAL
            game = Game(Bunner((240, -320)))
        elif key_just_pressed(keys.A):
            state = State.AUTO
            game = Game(Bunner((240, -320)))
        else:
            game.update()

    elif state == State.MANUAL or state == State.AUTO:
        # Is it game over?
        if game.bunner.state != PlayerState.ALIVE and game.bunner.timer < 0:
            # Update high score
            high_score = max(high_score, game.score())

            # Write high score file
            try:
                with open("high1.txt", "w") as file:
                    file.write(str(high_score))
            except:
                # If an error occurs writing the file, just ignore it and carry on, rather than crashing
                pass

            state = State.GAME_OVER
            game = Game(Bunner((240, -320)))
            state = State.AUTO
        else:
            game.update()

    elif state == State.GAME_OVER:
        # Switch to menu state, and create a new game object without a player
        if key_just_pressed(keys.SPACE):
            game.stop_looped_sounds()
            state = State.MENU
            game = Game()
            
    

def draw():
    game.draw()

    if state == State.MENU:
        screen.blit("title", (0, 0))
        screen.blit("start" + str([0, 1, 2, 1][game.scroll_pos // 6 % 4]), ((WIDTH - 270) // 2, HEIGHT - 240))
        screen.draw.text("PRESS A FOR AUTO MODE", ((WIDTH - 225) // 2, HEIGHT - 170))
        

    elif state == State.MANUAL or state == State.AUTO:
        # Display score and high score
        display_number(game.score(), 0, 0, 0)
        display_number(high_score, 1, WIDTH - 10, 1)

    elif state == State.GAME_OVER:
        # Display "Game Over" image
        screen.blit("gameover", (0, 0))

# Set up sound system
try:
    pygame.mixer.quit()
    pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(16)
except:
    # If an error occurs, just ignore it
    pass

# Load high score from file
try:
    with open("high1.txt", "r") as f:
        high_score = int(f.read())
except:
    # If opening the file fails (likely because it hasn't yet been created), set high score to 0
    high_score = 0

# Set the initial game state
state = State.MENU

# Create a new Game object, without a Player object
game = Game()

pgzrun.go()
