import pygame
from signalProcessing.alphaPowerCalculator import AlphaPowerCalculator
from .constants import BLACK, GRAVITY, SCREEN_HEIGHT


class Orb(pygame.sprite.Sprite):

    def __init__(self, color, width, height):
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        # Draw orb
        pygame.draw.rect(self.image, color, [0, 0, width, height])

        # initialize random velocity
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.rect = self.image.get_rect()

        self.alphaPowerCalculator = AlphaPowerCalculator(128, 128)
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
        # a solution to this would be to have a data collection period to start
        # with to determin min/max
        power = self.alphaPowerCalculator.get_power()
        if power > self.max_alpha and power < 5000:  # hard code because this is a demo, and not real yet
            self.max_alpha = power
        if power < self.min_alpha:
            self.min_alpha = power

        # normalize so that the float factor is between 0 and twice the force of gravity.
        # This value is arbitrary.
        self.float_factor = -(GRAVITY * 1.5) * (
            power - self.min_alpha) / (self.max_alpha - self.min_alpha)
        print("float_factor: ", self.float_factor)

    def handle_collision(self):
        if self.rect.bottom >= SCREEN_HEIGHT and abs(
                self.float_factor) < abs(GRAVITY):
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
        self.acceleration = [0, self.float_factor + GRAVITY]
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

    def apply_velocity(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
