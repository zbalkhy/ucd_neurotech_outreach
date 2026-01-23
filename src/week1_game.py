import pygame
import sys
import random

# ---------- Game Settings ----------
FPS = 60

# Colors (black & white only)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Player settings
PLAYER_SIZE = 40
PLAYER_X = 150  # fixed x position
MOVE_SPEED = 20  # pixels per frame for smooth movement

# Obstacle settings
OBSTACLE_WIDTH = 40
OBSTACLE_SPEED = 6
SPAWN_INTERVAL_MS = 1200  # how often to spawn obstacles

pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("Cube Infinite Runner (Black & White)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 32)

WIDTH, HEIGHT = screen.get_size()
TOP_LANE_Y = HEIGHT // 4 - PLAYER_SIZE // 2
BOTTOM_LANE_Y = (3 * HEIGHT) // 4 - PLAYER_SIZE // 2


class Player:
    def __init__(self):
        self.rect = pygame.Rect(PLAYER_X, BOTTOM_LANE_Y, PLAYER_SIZE, PLAYER_SIZE)
        self.target_y = BOTTOM_LANE_Y

    def update(self, keys):
        self.target_y = TOP_LANE_Y if keys[pygame.K_SPACE] else BOTTOM_LANE_Y

        if self.rect.y < self.target_y:
            self.rect.y = min(self.rect.y + MOVE_SPEED, self.target_y)
        elif self.rect.y > self.target_y:
            self.rect.y = max(self.rect.y - MOVE_SPEED, self.target_y)

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)


class Obstacle:
    def __init__(self, lane_type):
        self.rect = pygame.Rect(WIDTH, 0, OBSTACLE_WIDTH, HEIGHT // 2)
        self.rect.y = 0 if lane_type == "top" else HEIGHT // 2
        self.scored = False

    def update(self):
        self.rect.x -= OBSTACLE_SPEED

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

    def is_off_screen(self):
        return self.rect.right < 0


def draw_divider():
    pygame.draw.line(screen, WHITE, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 1)


def draw_text(text, x, y, center=False):
    img = font.render(text, True, WHITE)
    rect = img.get_rect()
    rect.center = (x, y) if center else (x, y)
    screen.blit(img, rect)


def main():
    player = Player()
    obstacles = []
    score = 0
    game_over = False

    SPAWN_OBS = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_OBS, SPAWN_INTERVAL_MS)

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                player = Player()
                obstacles = []
                score = 0
                game_over = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if not game_over and event.type == SPAWN_OBS:
                lane_type = random.choice(["top", "bottom"])
                obstacles.append(Obstacle(lane_type))

        if not game_over:
            player.update(keys)

            for obs in obstacles:
                obs.update()
                if player.rect.colliderect(obs.rect):
                    game_over = True
                if not obs.scored and obs.rect.right < player.rect.left:
                    obs.scored = True
                    score += 1

            obstacles = [obs for obs in obstacles if not obs.is_off_screen()]

        screen.fill(BLACK)
        draw_divider()

        player.draw(screen)
        for obs in obstacles:
            obs.draw(screen)

        draw_text(f"Score: {score}", WIDTH // 2, HEIGHT - 30, center=True)

        if game_over:
            draw_text("GAME OVER", WIDTH // 2, HEIGHT // 2 - 30, center=True)
            draw_text("Press R to Restart", WIDTH // 2, HEIGHT // 2 + 10, center=True)
            draw_text("Press ESC to Quit", WIDTH // 2, HEIGHT // 2 + 50, center=True)

        pygame.display.flip()


if __name__ == "__main__":
    main()
