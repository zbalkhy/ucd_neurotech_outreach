import pygame
import json
from time import sleep
from .constants import BLACK, WHITE, size, SCREEN_HEIGHT, SCREEN_WIDTH, GRAVITY
from .orb import Orb


class FloatTheOrb:
    def __init__(self):
        self.consumer = None 
        self.carryOn = True

    def __checkForNewDecision__(self) -> int:
        #TODO:: this is terrible
        newDecision = self.consumer.poll(timeout_ms=0)
        print("Pong:")
        if newDecision:
            for p in newDecision:
                for msg in newDecision[p]:
                    print(msg.value)
                    return msg.value
        return -1

    def InitializeAndRun(self):
        self.Initialize()
        self.Run()

    def Initialize(self):
        # TODO: turn this into an lsl reveiver
        #self.consumer = KafkaConsumer(self.decisionTopic, 
        #                    bootstrap_servers=self.kafkaServers,
        #                    value_deserializer=lambda m: json.loads(m.decode('ascii')))
        print("Pong:")
        #while not self.consumer.assignment():
            #print("not topics")
        #print("partition assigned")
        #self.consumer.seek_to_end()

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

            #Display scores:
            #font = pygame.font.Font(None, 74)
            #text = font.render(str(scoreA), 1, WHITE)
            #screen.blit(text, (10, 390))
            #text = font.render(str(scoreB), 1, WHITE)
            #screen.blit(text, (10, 270))
            
            # Update screen
            pygame.display.flip()

            # Limit to 60 frames per second
            clock.tick(60) 

        pygame.quit()