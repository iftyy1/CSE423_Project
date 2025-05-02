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



gun_pos = [0.0, 0.0, 0.0]
gun_angle = 0.0
car_colors = [(0.2, 0.2, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
car_color_index = 0

def get_random_obstacle_color():
    while True:
        r, g, b = random.uniform(0.2, 0.7), random.uniform(0.2, 0.7), random.uniform(0.2, 0.7)
        if not ((r > 0.7 and g < 0.3) or (g > 0.7 and r < 0.3)):
            return (r, g, b)

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
    for pos in collision_smoke:
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glutSolidSphere(5, 8, 8)
        glPopMatrix()        

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
                collision_smoke.append((gun_pos[0], gun_pos[1] + 10, gun_pos[2]))
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




def try_parking():
    global score, status_message
    for spot in parking_spots:
        dx = abs(gun_pos[0] - spot["x"])
        dz = abs(gun_pos[2] - spot["z"])
        if dx < 25 and dz < 25:
            if spot["type"] == "valid":
                score += 1
                status_message = "Parked Successfully!"
            elif spot["type"] == "no-parking":
                status_message = "NO PARKING ZONE!"
            return
    status_message = "Not in any parking spot"

def update_world():
    global gun_pos, last_valid_pos, skip_next_collision

    if skip_next_collision:
        skip_next_collision = False  
        last_valid_pos[:] = gun_pos[:]
        return

    if check_collision():
        gun_pos[:] = last_valid_pos[:]
    else:
        last_valid_pos[:] = gun_pos[:]

    while len(collision_smoke) > 5:
        collision_smoke.pop(0)


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
        x = minimap_x + MINIMAP_SIZE / 2 + spot["x"] * WORLD_SCALE
        y = minimap_y - MINIMAP_SIZE / 2 - spot["z"] * WORLD_SCALE

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
    px = minimap_x + MINIMAP_SIZE / 2 + gun_pos[0] * WORLD_SCALE
    py = minimap_y - MINIMAP_SIZE / 2 - gun_pos[2] * WORLD_SCALE
    glBegin(GL_TRIANGLES)
    glVertex2f(px, py + 5)
    glVertex2f(px - 4, py - 4)
    glVertex2f(px + 4, py - 4)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)



def showScreen():
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

    draw_text(10, WINDOW_HEIGHT - 40, f"Score: {score}")
    draw_text(10, WINDOW_HEIGHT - 60, f"{status_message}")
    draw_text(10, WINDOW_HEIGHT - 80, f"Camera: {'First Person' if first_person else 'Overhead'}")
    draw_text(10, WINDOW_HEIGHT - 100, f"Press 'M' to change car color & 'N' for day/night")

    draw_minimap()
    draw_damage_meter()

    glutSwapBuffers()

def keyboardListener(key, x, y):
    global gun_pos, gun_angle, first_person, car_color_index
    global transition_night, target_sky_color, damage
    global skip_next_collision 

    if damage >= max_damage:
        return 

    rad = math.radians(gun_angle)

    if key == b'w':
        gun_pos[0] += PLAYER_SPEED * math.sin(rad)
        gun_pos[2] += PLAYER_SPEED * math.cos(rad)
    elif key == b's':
        gun_pos[0] -= PLAYER_SPEED * math.sin(rad)
        gun_pos[2] -= PLAYER_SPEED * math.cos(rad)
    elif key == b'a':
        gun_angle = (gun_angle - ROTATE_SPEED) % 360
    elif key == b'd':
        gun_angle = (gun_angle + ROTATE_SPEED) % 360
    elif key == b'p':
        try_parking()
    elif key == b'r':
        gun_pos[:] = [0.0, 0.0, 0.0]
        gun_angle = 0.0
        last_valid_pos[:] = [0.0, 0.0, 0.0]
        collision_smoke.clear()
        damage = 0
        score = 0
        status_message = ""
        skip_next_collision = True 



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