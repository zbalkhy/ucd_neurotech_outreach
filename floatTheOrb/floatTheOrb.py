import pygame
import json
from time import sleep
from .constants import BLACK, WHITE, size, SCREEN_HEIGHT, SCREEN_WIDTH, GRAVITY
from .orb import Orb


class FloatTheOrb:
    def __init__(self):
        return

    def Run(self):
        print("Pong:running")
        pygame.init()

        # Open new window
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Float the Orb!")

        # Set up orb

        orb = Orb(WHITE, 40, 40)
        orb.rect.x = 345
        orb.rect.bottom = SCREEN_HEIGHT

        # Collect all game elements (paddles, and ball)
        all_sprites_list = pygame.sprite.Group()
        all_sprites_list.add(orb)

        carryOn = True
        clock = pygame.time.Clock()

        float_factor = 0
        # Game loop
        while carryOn:

            # Main event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    carryOn = False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_x:
                        carryOn = False

            # Game logic
            all_sprites_list.update()

            # Fill background
            screen.fill(BLACK)

            # Draw Sprites
            all_sprites_list.draw(screen)

            # Update screen
            pygame.display.flip()

            # Limit to 60 frames per second
            clock.tick(60) 

        pygame.quit()