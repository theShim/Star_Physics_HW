import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import random
import sys
import math
import time
import numpy as np
import json

from pygame_recorder import ScreenRecorder
from cutscenes import Cutscene
from background import Background

    ##############################################################################################

#initialising pygame stuff
pygame.init()  #general pygame
pygame.font.init() #font stuff
pygame.mixer.pre_init(44100, 16, 2, 4096) #music stuff
pygame.mixer.init()
pygame.event.set_blocked(None) #setting allowed events to reduce lag
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEWHEEL])
pygame.display.set_caption("")

#initalising pygame window
flags = pygame.DOUBLEBUF #| pygame.FULLSCREEN
SIZE = WIDTH, HEIGHT = (1080, 720)
screen = pygame.display.set_mode(SIZE, flags, 16)
clock = pygame.time.Clock()

#renaming common functions
vec = pygame.math.Vector2

#recording the screen
FPS = 60
recorder = ScreenRecorder(WIDTH, HEIGHT, FPS, out_file="test.mp4")

#useful functions
def gen_colour():
    colours = [
        (
            0, 
            random.randint(4, 64), 
            random.randint(123, 255)
        ),
        (
            random.randint(16, 76),
            random.randint(0, 57),
            random.randint(43, 103)
        ),
        (
            random.randint(34, 104),
            random.randint(67, 127),
            random.randint(134, 194),
        )
    ]
    return random.choice(colours)

def euclidean_distance(point1, point2):
    return vec(point1).distance_to(vec(point2))

    ##############################################################################################

GRAV = 9.81/4
FRIC = 0.95
WIND = 0

    ##############################################################################################

class Star(pygame.sprite.Sprite):
    def __init__(self, pos=None, radius=4, colour=None, mass=1, star=False):
        super().__init__()
        self.pos = vec(pos) if pos != None else vec(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50))
        self.old_pos = vec(self.pos.copy())
        self.mass = mass

        self.col = list(gen_colour()) if colour == None else list(colour)
        self.radius = radius
        self.held = False

        self.star = star
        if self.star:
            self.timer = random.uniform(0, math.pi*2)
            light = pygame.image.load("light.png").convert_alpha()
            for y in range(light.get_height()):
                for x in range(light.get_width()):
                    if light.get_at((x, y)) == (255, 255, 255, 255):
                        light.set_at((x, y), (255, 255, 255, 0))
            self.light = light
            self.stage = "gas"

    def move(self, dt):
        coords = self.pos.copy()
        old_coords = self.old_pos.copy()

        v = coords - old_coords
        v += vec(
          random.randrange(-245, 245)/100,
          random.randrange(-245, 245)/100
        )
        v *= 0.99
        v /= self.mass

        self.old_pos = coords
        self.pos = coords + v

    def collide_walls(self):
        coords = self.pos.copy()
        old_coords = self.old_pos.copy()
        v = coords - old_coords

        if coords.x > WIDTH - self.radius:
            self.pos.x = WIDTH - self.radius
            self.old_pos.x = self.pos.x + v.x
        if coords.x < self.radius:  
            self.pos.x = self.radius
            self.old_pos.x = self.pos.x + v.x

        if coords.y > HEIGHT - self.radius:
            self.pos.y = HEIGHT - self.radius
            self.old_pos.y = self.pos.y + v.y
        if coords.y < self.radius:  
            self.pos.y = self.radius
            self.old_pos.y = self.pos.y + v.y

    def collide_balls(self):
        for p in stars:
            if p != self:
                overlap = (self.radius * 2) - self.pos.distance_to(p.pos)
                if overlap > 0:
                    try:
                        distance = (self.pos - p.pos).normalize()
                    except ValueError:
                        distance = (self.pos - p.pos)
                    self.pos += distance/2
                    p.pos -= distance/2


    def orbit(self):
        if star.mass > 50:
            orbit_coords = star.pos.copy()
        else:
            if not pygame.mouse.get_pressed()[0]:#
                return
            orbit_coords = vec(pygame.mouse.get_pos())
        coords = self.pos.copy()

        v = orbit_coords - coords
        try:
            self.pos += v.normalize() * 2
        except:
            pass


    def star_combine(self):
        for p in stars:
            if p != self:
                if vec(p.pos).distance_to(self.pos) < self.radius:
                    if random.randint(1, 5) == 1:
                        self.radius += 0.1
                        self.mass += 0.1
                        stars.remove(p)


    def update(self, screen, dt, draw_flag: bool):

        if self.star:
            self.star_combine()

            if self.mass >= 150:
                self.stage = "red giant"
            elif self.mass >= 120:
                self.stage = "main sequence"
            elif self.mass > 60:
                self.stage = "protostar"

            if self.mass > 50:
                if self.pos.y > HEIGHT//2:
                    self.pos.y -= random.uniform(0, 1)
                elif self.pos.y < HEIGHT//2:
                    self.pos.y += random.uniform(0, 1)
            self.pos.y += random.uniform(-1, 1)

            self.timer += 0.075
            # particles.add(Trail(vec(self.pos.x, self.pos.y), self.col, (self.star, self.mass)))

        particles.add(Trail(self.pos.copy(), self.col, (self.star, self.mass)))

        self.move(dt)
        self.orbit()
        self.collide_walls()

        if draw_flag:
            self.draw(screen)

    def draw(self, screen):
        pygame.draw.circle(screen, self.col, self.pos, self.radius)

        if self.star:   
            if round(math.sin(self.timer), 1) == 0.0 and self.stage == "main sequence":
                particles.add(EnergyRing(self.pos.copy(), self.radius, self.col))
            x, y = self.pos.copy()
            r = self.radius * 1.2 if self.stage in ["gas", "red_giant"] else self.radius
            fluc = abs(math.sin(self.timer/8)) * 1.75

            if self.stage == "main sequence":
                light = pygame.transform.scale(self.light, (r*(2.75 - fluc), r*(2.75 - fluc)))
                screen.blit(light, list(map(lambda x:x-r*(2.75-fluc)/2, (x, y))), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                light = pygame.transform.scale(self.light, (r*(2.2 - fluc), r*(2.2 - fluc)))
                screen.blit(light, list(map(lambda x:x-r*(2.2-fluc)/2, (x, y))), special_flags=pygame.BLEND_RGBA_ADD)


class Trail(pygame.sprite.Sprite):
    def __init__(self, pos, colour, star):
        super().__init__()
        self.pos = pos
        self.opacity = 90
        self.star, self.mass = star
        
        if self.star:
            self.colour = [c-30 for c in list(colour)]
            for i, v in enumerate(colour):
                if v < 30: self.colour[i] = 30
        else:
            self.colour = list(colour)

    def update(self, screen):
        if self.star:
            if self.mass > 40: self.pos.x -= self.opacity/5
            self.opacity -= 4
        else:
            self.opacity -= 6

        if self.opacity < 10:
            particles.remove(self)
            return

        self.draw(screen)

    def draw(self, screen):
        pygame.draw.circle(screen, [c*self.opacity/100 for c in self.colour], self.pos, self.opacity/3 if self.star and star.mass > 40 else 2)

class EnergyRing(pygame.sprite.Sprite):
    def __init__(self, pos, radius, col):
        super().__init__()
        self.pos = pos
        self.radius = radius
        self.timer = 0
        self.colour = col

    def update(self, screen):
        self.radius += 1
        self.colour -= pygame.math.Vector3(1, 1, 1) * 4

        if self.colour.x < 0 and self.colour.y < 0 and self.colour.z < 0:
            particles.remove(self)
            return
        if self.colour.x < 0: self.colour.x = 0
        if self.colour.y < 0: self.colour.y = 0
        if self.colour.z < 0: self.colour.z = 0
        
        self.draw(screen)

    def draw(self, screen):
        pygame.draw.circle(screen, self.colour, self.pos, self.radius, 1)

    ##############################################################################################

stars = pygame.sprite.Group()
stars.add(star:=Star(colour=(128, 128, 96), radius=5, star=True))
for i in range(200):
    stars.add(Star(radius=4))

particles = pygame.sprite.Group()

c = Cutscene(star)

bg = Background()

    ##############################################################################################

last_time = time.time()

running = True
while running:

    dt = time.time() - last_time
    last_time = time.time()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

        elif event.type == pygame.MOUSEWHEEL:
            WIND += event.y / 10

    bg.update()
    screen.blit(bg.image, (0, 0))
    particles.update(screen)

    if star.mass < 60:
        if len(stars) < 400:
            stars.add(Star(radius=4) for i in range(8))
    stars.update(screen, dt, True)

    c.update()
    c.draw(screen, WIDTH, HEIGHT)
    
    # recorder.capture_frame(screen)    

    #fps
    # font = pygame.font.SysFont('monospace', 30)
    # fps = font.render(f'FPS: {int(clock.get_fps())}', True, (215, 215, 215))
    # screen.blit(fps, (0, 0))
    pygame.display.set_caption(f"FPS: {int(clock.get_fps())} | Mass: {round(star.mass, 2)} | Stage: {star.stage} | Visible Stars: {len(stars)-1}")

    pygame.display.update()
    clock.tick(FPS)

recorder.end_recording()

pygame.quit()
sys.exit()