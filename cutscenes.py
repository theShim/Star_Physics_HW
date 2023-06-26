import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    pygame.init()
    pygame.font.init()
    
import random
import sys
import math
import time
import numpy as np
import json

    ##############################################################################################

font = pygame.font.SysFont('monospace', (font_size:=36))

class Text(pygame.sprite.Sprite):
    def __init__(self, text, chunksize):
        self.words = text
        self.text = pygame.sprite.Group()
        self.split(text, chunksize)
        
        def find_width(text):
            e = {}
            for t in text:
                if t.pos.y not in list(e.keys()):
                    e[t.pos.y] = t.sprite.get_width()
                else:
                    e[t.pos.y] += t.sprite.get_width()
            try:
                width = max(list(e.values()))
            except:
                width = 0
            return width
        width = find_width(self.text)
        height = self.line_height + 40
        self.sprite = pygame.Surface((width, height), pygame.SRCALPHA)

        for t in self.text:
            self.sprite.blit(t.sprite, t.pos)
        
    def split(self, text, prevchunksize):
        colours = {
            "`w" : (255, 255, 255),
            "`y" : (255, 255, 0),
            "`o" : (255, 128, 0),
            "`r" : (255, 0, 0)
        }

        last_colour = "`w"
        line_start = 0
        self.line_height = -font_size

        blocks = text[:-1].split('#n')
        if len(blocks) != prevchunksize[0]:
            pygame.time.wait(300)
            prevchunksize[0] = len(blocks)
        block = blocks[-1]
        lines = block[:-1].split('\n')

        if "\n" in text:
            lines.pop(0)
        
        for t in lines:
            start = 0
            line_start = 0
            self.line_height += font_size

            for i, letter in enumerate(t):
                if letter == "`":
                    if t[i:i+2] in list(colours.keys()):
                        self.text.add(s:=Section(
                            text=t[start:i],
                            colour=colours[last_colour],
                            pos=pygame.math.Vector2(line_start, self.line_height)
                        ))
                        last_colour = t[i:i+2]
                        start = i+2
                        line_start += s.sprite.get_width()

            self.text.add(Section(
                text=t[start:],
                colour=colours[last_colour],
                pos=pygame.math.Vector2(line_start, self.line_height)
            ))

class Section(pygame.sprite.Sprite):
    def __init__(self, text, colour, pos):
        super().__init__()
        self.colour = colour
        self.pos = pos
        self.words = text
        self.sprite = font.render(text, True, self.colour)

    def __str__(self):
        return f"{self.colour} | {self.words} | {self.pos}"
    
# y = Text("Massive clouds of dust and mostly hydrogen known")
# pygame.image.save(y.sprite, "test1.png"); print("saved")
# x = Text("Massive clouds of dust and mostly hydrogen known`n as nebulae, apple")
# pygame.image.save(x.sprite, "test2.png"); print("saved")
# x = Text()
# pygame.image.save(x.sprite, "test3.png"); print("saved")

    ##############################################################################################

class Cutscene:
    def __init__(self, star):
        self.name = "life_cycle"
        self.step = 0
        self.timer = pygame.time.get_ticks()
        self.running = True

        self.star = star
        self.prev_chunksize = [0]

        self.text = {
            "protostar" : """
Massive clouds of dust and mostly hydrogen known
as `onebulae`w, are pulled together by the force of 
       gravity. This forms a `yprotostar`w.
""",
            "main sequence" : """
These hydrogen nuclei become hot enough to fuse, 
  which releases large amounts of heat energy. 
        It is now a `ymain sequence star`w.
""",
            "red giant" : """
Once all of the hydrogen has been fused, larger
 helium nuclei begin to form. This causes the
    star to expand and form a `rred giant`w.#n
Then it becomes another star or smthn
"""
        }
        self.text_counter = 0

    def update(self):
        keys = pygame.key.get_pressed()
        space = keys[pygame.K_SPACE]
        
        if self.step == 0: #txt | nebula turned into protostar
            if int(self.text_counter) < len(self.text["protostar"]):
                self.text_counter += 0.4
            else:
                if space:
                    self.step = 1
                    self.star.mass = 100

        elif self.step == 1: #protostar turning into main sequence
            self.star.mass += 0.05
            if self.star.mass < 120:
                self.star.radius += 0.05
                self.star.col[0] += 0.5
                if self.star.col[0] > 255: self.star.col[0] = 255
                self.star.col[1] += 0.5
                if self.star.col[1] > 255: self.star.col[1] = 255
                self.star.col[2] -= 0.5
                if self.star.col[2] < 0: self.star.col[2] = 0
            else:
                self.text_counter = 0
                self.prev_chunksize = [0]
                self.step = 2

        elif self.step == 2: #txt | protostar turned into main sequence star
            if int(self.text_counter) < len(self.text["main sequence"]):
                self.text_counter += 0.4
            else:
                if space:
                    self.step = 3
                    self.star.mass = 120

        elif self.step == 3: #main sequence turning into red giant
            self.star.mass += 0.075

            if self.star.mass < 150:
                self.star.radius += 0.1
                self.star.col[1] -= 0.5
                if self.star.col[1] < 0: self.star.col[1] = 0
            else:
                self.text_counter = 0
                self.prev_chunksize = [0]
                self.step = 4
                
        elif self.step == 4: #txt | main sequence turned into red giant
            if int(self.text_counter) < len(self.text['red giant']):
                self.text_counter += 0.4
            else:
                if space:
                    self.step = 5
                    self.star.mass = 150

        # elif self.step == 3: #white dwarf
        #     self.star.mass += 0.05
        #     self.radius -= 0.001

        #     if self.star.mass < 125:
        #         for i, c in self.star.col:
        #             self.star.col[i] = c + 0.5
        #             if self.star.col[i] > 255: self.star.col[i] = 255
        #     else:
        #         self.text_counter = 0
        #         self.step = 4

        # elif self.step == 4:
        #     if int(self.text_counter) < len(self.text["blackhole"]):
        #         self.text_counter += 0.4
        #     else:
        #         if space:
        #             self.step = 3

        return self.running
    
    def draw(self, screen, WIDTH,HEIGHT):

        if self.step in [0, 2, 4]:
            pygame.draw.rect(screen, (0, 0, 0), [0, 4.1*(HEIGHT//5), WIDTH, HEIGHT//5], border_top_left_radius=30, border_top_right_radius=30)

        if self.step == 0:
            text = Text(self.text["protostar"][0:int(self.text_counter)], self.prev_chunksize)
            screen.blit(text.sprite, (10, HEIGHT-text.sprite.get_height() - 10))

        elif self.step == 2:
            text = Text(self.text["main sequence"][0:int(self.text_counter)], self.prev_chunksize)
            screen.blit(text.sprite, (10, HEIGHT-text.sprite.get_height() - 10))

        elif self.step == 4:
            text = Text(self.text["red giant"][0:int(self.text_counter)], self.prev_chunksize)
            screen.blit(text.sprite, (10, HEIGHT-text.sprite.get_height() - 10))




class CutsceneManager:
    def __init__(self):
        self.scene = None
        self.running = False
        self.complete = []

        #######################################################

    def start_scene(self, scene):
        if scene.name not in self.complete:
            self.complete.append(scene.name)
            self.scene = scene
            self.running = True

    def end_scene(self):
        self.scene = None
        self.running = False

        #######################################################

    def update(self):
        if self.running:
            self.running = self.scene.update()
        else:
            self.end_scene()

    def draw(self, screen):
        self.scene.draw(screen)


# t = Text("""
# Once all of the hydrogen has been fused, larger
#  helium nuclei begin to form. This causes the
#     star to expand and form a `rred giant`w.#n
# Then it becomes another star or smthn.
# """)
# pygame.image.save(t.sprite, "test.png")