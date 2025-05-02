from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import sys
import time

WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
camera_pos = [0.0, 30.0, 400.0]
camera_angle = 0
camera_radius = 400
first_person = False

FOVY = 45
GRID_SIZE = 600
PLAYER_SPEED = 5
ROTATE_SPEED = 10

MINIMAP_SIZE = 150  
WORLD_SCALE = 0.2   

damage = 0
max_damage = 100
skip_next_collision = False

level = 1
max_level = 5
successful_parkings = 0

level_start_time = time.time()
level_duration = 60 
timer_paused = False


WORLD_BOUND_MIN_X = -300
WORLD_BOUND_MAX_X = 300
WORLD_BOUND_MIN_Z = -300
WORLD_BOUND_MAX_Z = 300


def is_within_boundary(x, z):
    return WORLD_BOUND_MIN_X <= x <= WORLD_BOUND_MAX_X and WORLD_BOUND_MIN_Z <= z <= WORLD_BOUND_MAX_Z

gun_pos = [0.0, 0.0, 0.0]
gun_angle = 0.0
car_colors = [(0.2, 0.2, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
car_color_index = 0

def get_random_obstacle_color():
    while True:
        r, g, b = random.uniform(0.2, 0.7), random.uniform(0.2, 0.7), random.uniform(0.2, 0.7)
        if not ((r > 0.7 and g < 0.3) or (g > 0.7 and r < 0.3)):
            return (r, g, b)

def is_position_occupied(x, z):
    for spot in parking_spots:
        if abs(spot["x"] - x) < 60 and abs(spot["z"] - z) < 60:
            return True
    return False


parking_spots = [
    {"x": 100, "z": 100, "color": (0, 1, 0), "type": "valid"},
    {"x": -150, "z": -100, "color": (1, 0, 0), "type": "no-parking"},
    {"x": 0, "z": 200, "color": (0.5, 0.5, 0.5), "type": "obstacle", "cube_color": get_random_obstacle_color()},
]


car_size = 20
score = 0
status_message = ""
collision_smoke = []
last_valid_pos = [0.0, 0.0, 0.0]

sky_color = [0.5, 0.7, 1.0]
target_sky_color = [0.5, 0.7, 1.0]
transition_night = False
transition_speed = 0.008


def draw_smoke():
    glColor3f(0.5, 0.5, 0.5)
    for smoke in collision_smoke:
        x, y, z = smoke["pos"]
        for _ in range(int(smoke["lifetime"] * 10)):  # fewer lines as it fades
            dx = random.uniform(-3, 3)
            dy = random.uniform(2, 6)
            dz = random.uniform(-3, 3)
            glBegin(GL_LINES)
            glVertex3f(x, y, z)
            glVertex3f(x + dx, y + dy, z + dz)
            glEnd()



def draw_road():
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-80, 0.05, -GRID_SIZE)
    glVertex3f(80, 0.05, -GRID_SIZE)
    glVertex3f(80, 0.05, GRID_SIZE)
    glVertex3f(-80, 0.05, GRID_SIZE)
    glEnd()
    glColor3f(1.0, 1.0, 0.0)
    for z in range(-GRID_SIZE, GRID_SIZE, 100):
        glBegin(GL_QUADS)
        glVertex3f(-10, 0.06, z)
        glVertex3f(10, 0.06, z)
        glVertex3f(10, 0.06, z + 40)
        glVertex3f(-10, 0.06, z + 40)
        glEnd()

def draw_surroundings():
    for i in range(-GRID_SIZE, GRID_SIZE, 50):
        for j in range(-GRID_SIZE, GRID_SIZE, 50):
            if abs(i) > 90 or abs(j) > 90:
                glColor3f(0.0, 0.5, 0.0)
                glBegin(GL_QUADS)
                glVertex3f(i, 0.01, j)
                glVertex3f(i + 50, 0.01, j)
                glVertex3f(i + 50, 0.01, j + 50)
                glVertex3f(i, 0.01, j + 50)
                glEnd()

def draw_grid():
    for i in range(-GRID_SIZE, GRID_SIZE, 50):
        for j in range(-GRID_SIZE, GRID_SIZE, 50):
            glColor3f(0.1 + ((i + GRID_SIZE) % 100) / 1000.0, 0.1, 0.1)
            glBegin(GL_QUADS)
            glVertex3f(i, 0, j)
            glVertex3f(i + 50, 0, j)
            glVertex3f(i + 50, 0, j + 50)
            glVertex3f(i, 0, j + 50)
            glEnd()

    for spot in parking_spots:
        x, z = spot["x"], spot["z"]
        s = 30

        glColor3f(*spot["color"])
        glBegin(GL_QUADS)
        glVertex3f(x - s, 0.1, z - s)
        glVertex3f(x + s, 0.1, z - s)
        glVertex3f(x + s, 0.1, z + s)
        glVertex3f(x - s, 0.1, z + s)
        glEnd()

        if spot["type"] == "obstacle":
            glColor3f(*spot.get("cube_color", (0.6, 0.6, 0.6))) 
            glPushMatrix()
            glTranslatef(x, 8, z)        
            glScalef(0.8, 0.8, 0.8)     
            glutSolidCube(20)
            glPopMatrix()


def draw_player():
    global car_color_index
    color = car_colors[car_color_index % len(car_colors)]
    glPushMatrix()
    glTranslatef(gun_pos[0], gun_pos[1], gun_pos[2])
    glRotatef(gun_angle, 0, 1, 0)
    glColor3f(*color)
    glPushMatrix()
    glScalef(1, 0.4, 1.5)
    glutSolidCube(car_size)
    glPopMatrix()
    glColor3f(0.5, 0.5, 1.0)
    glPushMatrix()
    glTranslatef(0, car_size * 0.2, 0)
    glScalef(0.6, 0.3, 1.2)
    glutSolidCube(car_size)
    glPopMatrix()
    glColor3f(1, 1, 1)
    glPushMatrix()
    glTranslatef(7, 3, car_size * 0.75)
    glutSolidSphere(2, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-7, 3, car_size * 0.75)
    glutSolidSphere(2, 10, 10)
    glPopMatrix()
    glPopMatrix()

def check_collision():
    global damage
    for spot in parking_spots:
        if spot["type"] == "obstacle":
            dx = gun_pos[0] - spot["x"]
            dz = gun_pos[2] - spot["z"]
            if abs(dx) < car_size and abs(dz) < car_size:
                collision_smoke.append({
                    "pos": (gun_pos[0], gun_pos[1] + 10, gun_pos[2]),
                    "lifetime": 1.0  # starts fully visible
                })
                damage = min(max_damage, damage + 10)
                return True
    return False

def draw_damage_meter():
    MINIMAP_SIZE = 150
    MINIMAP_OFFSET_X = 180
    MINIMAP_OFFSET_Y = 10
    DAMAGE_OFFSET_Y = 20  

    bar_width = MINIMAP_SIZE
    bar_height = 15

    x = WINDOW_WIDTH - MINIMAP_OFFSET_X
    y = WINDOW_HEIGHT - MINIMAP_OFFSET_Y - MINIMAP_SIZE - DAMAGE_OFFSET_Y - bar_height

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1, 1, 1)
    glRasterPos2f(x, y + bar_height + 5)
    for ch in "Damage:":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()

    damage_ratio = damage / max_damage
    if damage_ratio < 0.3:
        glColor3f(0.0, 1.0, 0.0)  # green
    elif damage_ratio < 0.7:
        glColor3f(1.0, 1.0, 0.0)  # yellow
    else:
        glColor3f(1.0, 0.0, 0.0)  # red

    filled = bar_width * damage_ratio
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + filled, y)
    glVertex2f(x + filled, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()

    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + bar_height)
    glVertex2f(x, y + bar_height)
    glEnd()

    percent_text = f"{int(damage_ratio * 100)}%"
    glColor3f(1, 1, 1)
    glRasterPos2f(x + bar_width + 5, y + 3)
    for ch in percent_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def is_position_occupied(x, z, spots, threshold=60):
    for s in spots:
        if abs(s["x"] - x) < threshold and abs(s["z"] - z) < threshold:
            return True
    return False


def place_new_valid_spot():
    while True:
        x = random.randint(WORLD_BOUND_MIN_X + 50, WORLD_BOUND_MAX_X - 50)
        z = random.randint(WORLD_BOUND_MIN_Z + 50, WORLD_BOUND_MAX_Z - 50)

        if is_within_boundary(x, z) and not is_position_occupied(x, z, parking_spots):
            parking_spots.append({"x": x, "z": z, "color": (0, 1, 0), "type": "valid"})
            break


def place_new_red_zone():
    while True:
        x = random.randint(WORLD_BOUND_MIN_X + 50, WORLD_BOUND_MAX_X - 50)
        z = random.randint(WORLD_BOUND_MIN_Z + 50, WORLD_BOUND_MAX_Z - 50)

        if is_within_boundary(x, z) and not is_position_occupied(x, z, parking_spots):
            parking_spots.append({"x": x, "z": z, "color": (1, 0, 0), "type": "no-parking"})
            break


def place_new_obstacle():
    while True:
        x = random.randint(WORLD_BOUND_MIN_X + 50, WORLD_BOUND_MAX_X - 50)
        z = random.randint(WORLD_BOUND_MIN_Z + 50, WORLD_BOUND_MAX_Z - 50)

        if is_within_boundary(x, z) and not is_position_occupied(x, z, parking_spots):
            color = get_random_obstacle_color()
            parking_spots.append({"x": x, "z": z, "color": (0.5, 0.5, 0.5), "type": "obstacle", "cube_color": color})
            break


def reset_game_due_to_timeout():
    global score, level, damage, gun_pos, gun_angle, last_valid_pos, status_message
    global collision_smoke, skip_next_collision, parking_spots, level_start_time, successful_parkings

    status_message = "Time's Up! Restarting from Level 1"
    score = 0
    level = 1
    damage = 0
    successful_parkings = 0
    gun_pos[:] = [0.0, 0.0, 0.0]
    gun_angle = 0.0
    last_valid_pos[:] = [0.0, 0.0, 0.0]
    collision_smoke.clear()
    skip_next_collision = True
    level_start_time = time.time()

    parking_spots[:] = [
        {"x": 100, "z": 100, "color": (0, 1, 0), "type": "valid"},
        {"x": -150, "z": -100, "color": (1, 0, 0), "type": "no-parking"},
        {"x": 0, "z": 200, "color": (0.5, 0.5, 0.5), "type": "obstacle", "cube_color": get_random_obstacle_color()},
    ]



def try_parking():
    global score, status_message, successful_parkings, level, level_start_time

    for spot in parking_spots:
        dx = abs(gun_pos[0] - spot["x"])
        dz = abs(gun_pos[2] - spot["z"])
        if dx < 25 and dz < 25:
            if spot["type"] == "valid":
                score += 1
                successful_parkings += 1
                status_message = f"Parked Successfully! Score: {score}"

                parking_spots.remove(spot)
                place_new_valid_spot()

                # Level up every 3 valid parks
                if successful_parkings % 3 == 0 and level < 5:
                    level += 1
                    level_start_time = time.time()
                    status_message = f"🏆 Level UP! Now Level {level}"
                    for _ in range(level):
                        place_new_obstacle()
                        place_new_red_zone()
                elif level == 5 and successful_parkings % 3 == 0:
                    status_message = "Complete all levels!"

            elif spot["type"] == "no-parking":
                score = max(0, score - 2)
                status_message = "NO PARKING ZONE! -2 Points"
            elif spot["type"] == "obstacle":
                status_message = "Can't park here! It's an obstacle."
            return

    status_message = "!!Not in any parking spot"





def update_world():
    global gun_pos, last_valid_pos, skip_next_collision, status_message, timer_paused

    if skip_next_collision:
        skip_next_collision = False  
        last_valid_pos[:] = gun_pos[:]
        return

    if damage >= max_damage:
        status_message = "Game Over!"
        timer_paused = True 
        return  

    if check_collision():
        gun_pos[:] = last_valid_pos[:]
    else:
        last_valid_pos[:] = gun_pos[:]

    while len(collision_smoke) > 5:
        collision_smoke.pop(0)
    
    for smoke in collision_smoke:
        smoke["lifetime"] -= 0.02

    collision_smoke[:] = [s for s in collision_smoke if s["lifetime"] > 0]


def update_sky_color():
    for i in range(3):
        if abs(sky_color[i] - target_sky_color[i]) > 0.01:
            if sky_color[i] < target_sky_color[i]:
                sky_color[i] += transition_speed
            else:
                sky_color[i] -= transition_speed

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_minimap():
    MINIMAP_SIZE = 150
    WORLD_SCALE = 0.2
    MINIMAP_OFFSET_X = 180 
    MINIMAP_OFFSET_Y = 10   

    minimap_x = WINDOW_WIDTH - MINIMAP_OFFSET_X
    minimap_y = WINDOW_HEIGHT - MINIMAP_OFFSET_Y

    def map_to_minimap(val, center, scale):
        screen_val = center + val * scale
        return max(center - MINIMAP_SIZE / 2 + 4, min(screen_val, center + MINIMAP_SIZE / 2 - 4))

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(minimap_x, minimap_y)
    glVertex2f(minimap_x + MINIMAP_SIZE, minimap_y)
    glVertex2f(minimap_x + MINIMAP_SIZE, minimap_y - MINIMAP_SIZE)
    glVertex2f(minimap_x, minimap_y - MINIMAP_SIZE)
    glEnd()

    for spot in parking_spots:
        x = map_to_minimap(spot["x"], minimap_x + MINIMAP_SIZE / 2, WORLD_SCALE)
        y = map_to_minimap(-spot["z"], minimap_y - MINIMAP_SIZE / 2, WORLD_SCALE)

        if spot["type"] == "valid":
            glColor3f(0, 1, 0)
        elif spot["type"] == "no-parking":
            glColor3f(1, 0, 0)
        elif spot["type"] == "obstacle":
            glColor3f(0.5, 0.5, 0.5)

        glBegin(GL_QUADS)
        glVertex2f(x - 4, y - 4)
        glVertex2f(x + 4, y - 4)
        glVertex2f(x + 4, y + 4)
        glVertex2f(x - 4, y + 4)
        glEnd()

    glColor3f(0.2, 0.2, 1.0)
    px = map_to_minimap(gun_pos[0], minimap_x + MINIMAP_SIZE / 2, WORLD_SCALE)
    py = map_to_minimap(-gun_pos[2], minimap_y - MINIMAP_SIZE / 2, WORLD_SCALE)
    glBegin(GL_TRIANGLES)
    glVertex2f(px, py + 5)
    glVertex2f(px - 4, py - 4)
    glVertex2f(px + 4, py - 4)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def reset_game_state():
    global level, score, damage, gun_pos, gun_angle, last_valid_pos
    global collision_smoke, skip_next_collision, level_start_time
    global parking_spots, timer_paused, successful_parks, status_message

    level = 1
    score = 0
    damage = 0
    successful_parks = 0
    timer_paused = False
    level_start_time = time.time()
    skip_next_collision = True
    status_message = ""

    gun_pos[:] = [0.0, 0.0, 0.0]
    gun_angle = 0.0
    last_valid_pos[:] = [0.0, 0.0, 0.0]
    collision_smoke.clear()

    parking_spots[:] = [
        {"x": 100, "z": 100, "color": (0, 1, 0), "type": "valid"},
        {"x": -150, "z": -100, "color": (1, 0, 0), "type": "no-parking"},
        {"x": 0, "z": 200, "color": (0.5, 0.5, 0.5), "type": "obstacle", "cube_color": get_random_obstacle_color()},
    ]


def showScreen():
    global time_left, status_message,max_level,max_damage

    update_sky_color()
    glClearColor(*sky_color, 1)
    glClear(GL_COLOR_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()

    draw_surroundings()
    draw_road()
    draw_grid()
    draw_smoke()
    draw_player()

    # Timer logic (do this before displaying)
    if not timer_paused and damage < max_damage and level < max_level:
        time_left = max(0, int(60 - (time.time() - level_start_time)))
        if time_left == 0:
            # Time expired, reset everything
            status_message = "Time's up! Back to Level 1"
            reset_game_state()
    elif damage >= max_damage:
        time_left = 0  # Stop timer display if damaged

    # UI Text
    draw_text(10, WINDOW_HEIGHT - 40, f"Score: {score}")
    draw_text(10, WINDOW_HEIGHT - 60, f"{status_message}")
    draw_text(10, WINDOW_HEIGHT - 80, f"Camera: {'First Person' if first_person else 'Overhead'}")
    draw_text(10, WINDOW_HEIGHT - 100, f"Press 'M' to change car color & 'N' for day/night")
    draw_text(10, WINDOW_HEIGHT - 120, f"Level: {level}")
    draw_text(10, WINDOW_HEIGHT - 140, f"Time Left: {time_left}s")  # Timer display

    draw_minimap()
    draw_damage_meter()
    glutSwapBuffers()




def keyboardListener(key, x, y):
    global gun_pos, gun_angle, first_person, car_color_index
    global transition_night, target_sky_color, damage, timer_paused
    global skip_next_collision, level, successful_parkings, score, level_start_time, status_message

    if damage >= max_damage and key != b'r':
        return 

    rad = math.radians(gun_angle)

    if key == b'w':
        new_x = gun_pos[0] + PLAYER_SPEED * math.sin(rad)
        new_z = gun_pos[2] + PLAYER_SPEED * math.cos(rad)
        if is_within_boundary(new_x, new_z):
            gun_pos[0] = new_x
            gun_pos[2] = new_z
    elif key == b's':
        new_x = gun_pos[0] - PLAYER_SPEED * math.sin(rad)
        new_z = gun_pos[2] - PLAYER_SPEED * math.cos(rad)
        if is_within_boundary(new_x, new_z):
            gun_pos[0] = new_x
            gun_pos[2] = new_z
    elif key == b'a':
        gun_angle = (gun_angle - ROTATE_SPEED) % 360
    elif key == b'd':
        gun_angle = (gun_angle + ROTATE_SPEED) % 360
    elif key == b'p':
        try_parking()
    elif key == b'r':
        reset_game_state()


    elif key == b'v':
        first_person = not first_person
    elif key == b'm':
        car_color_index = (car_color_index + 1) % len(car_colors)
    elif key == b'n':
        if not transition_night:
            target_sky_color = [0.0, 0.0, 0.0]
            transition_night = True
        else:
            target_sky_color = [0.5, 0.7, 1.0]
            transition_night = False

def specialKeyListener(key, x, y):
    global camera_pos, camera_angle

    if key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle - 5) % 360
    elif key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle + 5) % 360
    elif key == GLUT_KEY_UP:
        camera_pos[1] += 10
    elif key == GLUT_KEY_DOWN:
        camera_pos[1] = max(camera_pos[1] - 10, 50)

    rad = math.radians(camera_angle)
    camera_pos[0] = gun_pos[0] + camera_radius * math.sin(rad)
    camera_pos[2] = gun_pos[2] + camera_radius * math.cos(rad)


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        eye = (gun_pos[0], gun_pos[1] + 15, gun_pos[2])
        dir_rad = math.radians(gun_angle)
        center = (eye[0] + math.sin(dir_rad) * 100, eye[1], eye[2] + math.cos(dir_rad) * 100)
        gluLookAt(*eye, *center, 0, 1, 0)
    else:
        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],
            gun_pos[0], 0, gun_pos[2],
            0, 1, 0
        )

def idle():
    update_world()
    glutPostRedisplay()

def init_entities():
    global score, status_message, gun_pos, gun_angle, collision_smoke
    score = 0
    status_message = ""
    gun_pos[:] = [0.0, 0.0, 0.0]
    gun_angle = 0.0
    collision_smoke = []

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Parking Simulation")
    init_entities()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
