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
from scipy.spatial import Voronoi

import pstats
import cProfile

    ##############################################################################################

#initialising pygame stuff
pygame.init()  #general pygame
pygame.font.init() #font stuff
pygame.mixer.pre_init(44100, 16, 2, 4096) #music stuff
pygame.mixer.init()
pygame.event.set_blocked(None) #setting allowed events to reduce lag
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
pygame.display.set_caption("")

#initalising pygame window
flags = pygame.DOUBLEBUF #| pygame.FULLSCREEN
SIZE = WIDTH, HEIGHT = (1200, 720)
screen = pygame.display.set_mode(SIZE, flags, 16)
clock = pygame.time.Clock()

#renaming common functions
vec = pygame.math.Vector2

#useful functions
def gen_colour():
    return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

def euclidean_distance(point1, point2):
    return vec(point1).distance_to(vec(point2))

    ##############################################################################################

def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite
    regions.

    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.

    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.

    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1] # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)

def find_centre(points):
    x = 0
    y = 0
    for p in points:
        x += p[0]
        y += p[1]
    return (x/len(points), y/len(points))


class Background(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.particles = pygame.sprite.Group()
        for i in range(50): self.particles.add(Particle())

        self.stars = pygame.sprite.Group()
        for i in range(30): self.stars.add(Star())

    def voronoi(self):

        points = list(map(lambda p:p.pos, self.particles))
        vor = Voronoi(points)
        regions, vertices = voronoi_finite_polygons_2d(vor)
        for region in regions:
            polygon = vertices[region]
            polygon = [list(p) for p in polygon]
        
            y = find_centre(polygon)[1]
            if y < HEIGHT//10:
                c = (9, 88, 110)
            elif y < 2*HEIGHT//10:
                c = (18, 90, 122)
            elif y < 3*HEIGHT//10:
                c = (25, 89, 130)
            elif y < 4*HEIGHT//10:
                c = (36, 89, 145)
            elif y < 5*HEIGHT//10:
                c = (48, 92, 157)
            elif y < 6*HEIGHT//10:
                c = (63, 93, 174)
            elif y < 7*HEIGHT//10:
                c = (73, 92, 187)
            elif y < 8*HEIGHT//10:
                c = (79, 76, 174)
            elif y < 9*HEIGHT//10:
                c = (79, 95, 187)
            else:
                c = (84, 105, 195)

            c = pygame.math.Vector3(c) - pygame.math.Vector3(100, 100, 100)
            for i, j in enumerate(c):
                if j < 0:
                    c[i] = 0
            pygame.draw.polygon(self.image, c, polygon)
        # for v in vertices:
        #     pygame.draw.circle(self.image, (0, 0, 0), v, 2)

        self.particles.update()

    def update(self):
        self.image.fill((0,0,0))
        # self.voronoi()
        
        self.stars.update(self.image)

class Particle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.start, self.end = 0, WIDTH
        self.pos = vec(random.randint(5, WIDTH-5), random.randint(5, HEIGHT-5))
        self.vel = vec(random.randint(-360, 360), random.randint(-360, 360)).normalize()
        self.speed = 0.5

    def move(self):
        self.pos += self.vel * self.speed

        if self.pos.x < self.start or self.pos.x > self.end:
            self.vel.x *= -1
        if self.pos.y < self.start or self.pos.y > HEIGHT:
            self.vel.y *= -1

    def update(self):
        self.move()


class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.pos = vec(random.randint(5, WIDTH-5), random.randint(5, HEIGHT-5))
        self.radius = random.randint(2, 4)
        self.timer = random.randint(1, 1000)

        self.vel = vec(random.randint(10, 20), 0) * -1 / 20

    def move(self):
        self.pos += self.vel

        if self.pos.x < 0:
            self.pos.x = WIDTH

    def update(self, screen):
        self.timer += 1
        self.move()
        self.draw(screen)

    def draw(self, screen):
        radius = math.sin(self.timer * 0.05) * self.radius
        pygame.draw.circle(screen, (255, 255, 255), self.pos, radius)

# bg = Background()

#     #############################################################################################

# profiler = cProfile.Profile()
# profiler.enable()

# last_time = time.time()

# running = True
# while running:

#     dt = time.time() - last_time
#     last_time = time.time()
    
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         elif event.type == pygame.KEYDOWN:
#             if event.key == pygame.K_q:
#                 running = False

#     screen.fill((30, 30, 30))

#     bg.update()
#     screen.blit(bg.image, (0, 0))

#     #fps
#     font = pygame.font.SysFont('monospace', 30)
#     fps = font.render(f'FPS: {int(clock.get_fps())}', True, (215, 215, 215))
#     screen.blit(fps, (0, 0))

#     pygame.display.update()
#     clock.tick(60)

# pygame.quit()
# sys.exit()