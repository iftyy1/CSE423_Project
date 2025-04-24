from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import sys

WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 800
camera_pos = [0.0, 500.0, 500.0]
first_person = False

FOVY = 60
GRID_SIZE = 600
PLAYER_SPEED = 5
ROTATE_SPEED = 10

gun_pos = [0.0, 0.0, 0.0]
gun_angle = 0.0

# Parking simulation variables
parking_spots = [
    {"x": 100, "z": 100, "color": (0, 1, 0), "type": "valid"},
    {"x": -150, "z": -100, "color": (1, 0, 0), "type": "no-parking"},
    {"x": 0, "z": 200, "color": (0.5, 0.5, 0.5), "type": "obstacle"},
]
car_size = 20
score = 0
status_message = ""
collision_smoke = []

def draw_smoke():
    glColor3f(0.5, 0.5, 0.5)
    for pos in collision_smoke:
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glutSolidSphere(5, 8, 8)
        glPopMatrix()

def draw_grid():
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-GRID_SIZE, GRID_SIZE + 1, 50):
        glVertex3f(i, 0, -GRID_SIZE)
        glVertex3f(i, 0, GRID_SIZE)
        glVertex3f(-GRID_SIZE, 0, i)
        glVertex3f(GRID_SIZE, 0, i)
    glEnd()

    for spot in parking_spots:
        glColor3f(*spot["color"])
        x, z = spot["x"], spot["z"]
        s = 30
        glBegin(GL_QUADS)
        glVertex3f(x - s, 0.1, z - s)
        glVertex3f(x + s, 0.1, z - s)
        glVertex3f(x + s, 0.1, z + s)
        glVertex3f(x - s, 0.1, z + s)
        glEnd()

def draw_player():
    glPushMatrix()
    glTranslatef(gun_pos[0], gun_pos[1], gun_pos[2])
    glRotatef(gun_angle, 0, 1, 0)
    glColor3f(0.2, 0.2, 1.0)
    glPushMatrix()
    glScalef(1, 0.5, 2)
    glutSolidCube(car_size)
    glPopMatrix()
    glPopMatrix()

def check_collision():
    for spot in parking_spots:
        if spot["type"] == "obstacle":
            dx = gun_pos[0] - spot["x"]
            dz = gun_pos[2] - spot["z"]
            if abs(dx) < car_size and abs(dz) < car_size:
                collision_smoke.append((gun_pos[0], gun_pos[1] + 10, gun_pos[2]))
                return True
    return False

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
    check_collision()
    while len(collision_smoke) > 5:
        collision_smoke.pop(0)

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

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()
    glEnable(GL_DEPTH_TEST)
    draw_grid()
    draw_player()
    draw_smoke()
    glDisable(GL_DEPTH_TEST)
    draw_text(10, WINDOW_HEIGHT - 20, f"Score: {score}")
    draw_text(10, WINDOW_HEIGHT - 40, f"{status_message}")
    glutSwapBuffers()

def keyboardListener(key, x, y):
    global gun_pos, gun_angle
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
        collision_smoke.clear()

def specialKeyListener(key, x, y):
    if key == GLUT_KEY_UP:
        camera_pos[1] += 10
    elif key == GLUT_KEY_DOWN:
        camera_pos[1] -= 10
    elif key == GLUT_KEY_LEFT:
        camera_pos[0] -= 10
    elif key == GLUT_KEY_RIGHT:
        camera_pos[0] += 10

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        eye = tuple(gun_pos)
        dir_rad = math.radians(gun_angle)
        center = (eye[0] + math.sin(dir_rad)*100, eye[1], eye[2] + math.cos(dir_rad)*100)
        gluLookAt(*eye, *center, 0, 1, 0)
    else:
        gluLookAt(*camera_pos, 0, 0, 0, 0, 1, 0)

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
    glEnable(GL_DEPTH_TEST)
    init_entities()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
