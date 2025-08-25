import os
from common import BLACK, WHITE, PYGAME_WINDOW_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH, GRAVITY
import pygame
import platform
import threading
from threading import Lock
from common import *
import tkinter as tk

class Orb(pygame.sprite.Sprite):
    def __init__(self, color, width, height, user_context: dict):
        super().__init__()

        self.user_context = user_context

        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        
        # Draw orb
        pygame.draw.rect(self.image, color, [0, 0, width, height])

        # initialize random velocity
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.rect = self.image.get_rect()

        #self.alphaPowerCalculator = AlphaPowerCalculator(128, 128)
        self.float_factor = 0
        self.max_alpha = 0
        self.min_alpha = float('inf')

    def get_key_pressed(self):
            # if the up key is pressed increase the float factor to a certain value
            # if no keys are pressed, don't increase the float factor
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                self.float_factor = -0.07
            if not keys[pygame.K_w]:
                self.float_factor = 0
    
    def get_alpha_float_factor(self):
        # float factor is calculated from power based on a "rolling" normalization of the power
        # it should be a litte erratic at first, but eventaully it will calm down. 
        # a solution to this would be to have a data collection period to start with to determin min/max
        if len(self.user_context[RAW_DATA]):
            power = self.user_context[RAW_DATA][-1]
        else:
            power = 0

        if power > self.max_alpha and power < 5000: # hard code because this is a demo, and not real yet
            self.max_alpha = power
        if power < self.min_alpha:
            self.min_alpha = power
        
        # normalize so that the float factor is between 0 and twice the force of gravity.
        # This value is arbitrary.
        self.float_factor = power #-(GRAVITY*1.5)*(power - self.min_alpha)/(self.max_alpha - self.min_alpha)

    def handle_collision(self):
        if self.rect.bottom >= SCREEN_HEIGHT and abs(self.float_factor) < abs(GRAVITY):
            self.velocity[1] = 0
            self.rect.bottom = SCREEN_HEIGHT

        if self.rect.top <= 0:
            if self.float_factor and abs(self.float_factor) >= abs(GRAVITY):
                self.velocity[1] = 0
                self.rect.top = 0
    
    def update(self):
        self.get_alpha_float_factor()
        self.apply_acceleration()
        self.apply_velocity()
        self.handle_collision()

    def apply_acceleration(self):
        self.acceleration=[0, self.float_factor+GRAVITY]
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

    def apply_velocity(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

class FloatTheOrb(object):
    def __init__(self, root: tk.Toplevel, user_context: dict, user_context_lock: Lock):
        self.root = root
        self.frame = tk.Frame(self.root)
        self.user_context = user_context
        self.user_context_lock = user_context_lock
        self.game_started = False
        return

    def start_pygame(self):
        pygame.init()
        self.win = pygame.display.set_mode(PYGAME_WINDOW_SIZE)
        self.win.fill(BLACK)
        
        self.root.after(60, self.play_tk)

    def update(self):
        quit_pygame = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_pygame = True
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_x:
                    quit_pygame=True

        if quit_pygame:
            pygame.quit()
        else:
            self.all_sprites_list.update()
            self.win.fill(BLACK)
            self.all_sprites_list.draw(pygame.display.get_surface())
            pygame.display.flip()
        
            self.root.after(60, self.update)

    def play_tk(self):
        # Set up the orb
        orb = Orb(WHITE, 40, 40, self.user_context)
        orb.rect.x = 345
        orb.rect.bottom = SCREEN_HEIGHT

        # Collect all game elements (paddles, and ball)
        self.all_sprites_list = pygame.sprite.Group()
        self.all_sprites_list.add(orb)

        self.root.after(60, self.update)

if __name__ == "__main__":
    floatTheOrb = FloatTheOrb()
    floatTheOrb.Run()