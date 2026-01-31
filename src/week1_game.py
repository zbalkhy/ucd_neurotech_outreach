import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Headless Pygame

import tkinter as tk
import threading
import pygame
import random
from PIL import Image, ImageTk
from time import sleep

# --- Pygame Game Class ---
class InfiniteRunner:
    def __init__(self, size, fps):
        self.width = size[0]
        self.height = size[1]
        self.fps = fps
        self.screen = None
        self.running = True
        self.clock = pygame.time.Clock()
        self.font = None
        
        # Game state
        self.player = None
        self.obstacles = []
        self.score = 0
        self.game_over = False
        
        # Keyboard state (controlled by Tkinter)
        self.space_pressed = False
        self.r_pressed = False
        
        # Settings
        self.PLAYER_SIZE = 40
        self.PLAYER_X = 150
        self.MOVE_SPEED = 20
        self.OBSTACLE_WIDTH = 40
        self.OBSTACLE_SPEED = 6
        self.SPAWN_INTERVAL_MS = 1200
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        
        # Lane positions
        self.TOP_LANE_Y = self.height // 4 - self.PLAYER_SIZE // 2
        self.BOTTOM_LANE_Y = (3 * self.height) // 4 - self.PLAYER_SIZE // 2
        
        # Timer
        self.last_spawn_time = 0

    def start(self):
        """Start the Pygame loop in a separate thread."""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        """Pygame main loop."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.font = pygame.font.SysFont("consolas", 32)
        
        # Initialize game
        self.player = self.Player(self)
        self.last_spawn_time = pygame.time.get_ticks()

        while self.running:
            self.clock.tick(self.fps)
            current_time = pygame.time.get_ticks()

            # Handle restart with R key
            if self.game_over and self.r_pressed:
                self.reset_game()
                self.r_pressed = False  # Reset the flag

            # Spawn obstacles at intervals
            if not self.game_over and current_time - self.last_spawn_time > self.SPAWN_INTERVAL_MS:
                lane_type = random.choice(["top", "bottom"])
                self.obstacles.append(self.Obstacle(self, lane_type))
                self.last_spawn_time = current_time

            if not self.game_over:
                self.player.update()

                for obs in self.obstacles:
                    obs.update()
                    if self.player.rect.colliderect(obs.rect):
                        self.game_over = True
                    if not obs.scored and obs.rect.right < self.player.rect.left:
                        obs.scored = True
                        self.score += 1

                self.obstacles = [obs for obs in self.obstacles if not obs.is_off_screen()]

            self.draw()
            pygame.display.flip()

    def reset_game(self):
        """Reset the game state."""
        self.player = self.Player(self)
        self.obstacles = []
        self.score = 0
        self.game_over = False

    def draw(self):
        """Draw all game elements."""
        self.screen.fill(self.BLACK)
        
        # Draw divider
        pygame.draw.line(self.screen, self.WHITE, (0, self.height // 2), 
                        (self.width, self.height // 2), 1)
        
        # Draw player and obstacles
        self.player.draw(self.screen)
        for obs in self.obstacles:
            obs.draw(self.screen)
        
        # Draw score
        self.draw_text(f"Score: {self.score}", self.width // 2, self.height - 30, center=True)
        
        # Draw game over text
        if self.game_over:
            self.draw_text("GAME OVER", self.width // 2, self.height // 2 - 30, center=True)
            self.draw_text("Press R to Restart", self.width // 2, self.height // 2 + 10, center=True)

    def draw_text(self, text, x, y, center=False):
        """Helper to draw text."""
        img = self.font.render(text, True, self.WHITE)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(img, rect)

    # --- Inner Classes ---
    class Player:
        def __init__(self, game):
            self.game = game
            self.rect = pygame.Rect(game.PLAYER_X, game.BOTTOM_LANE_Y, 
                                   game.PLAYER_SIZE, game.PLAYER_SIZE)
            self.target_y = game.BOTTOM_LANE_Y

        def update(self):
            # Check the game's space_pressed flag instead of pygame keys
            self.target_y = self.game.TOP_LANE_Y if self.game.space_pressed else self.game.BOTTOM_LANE_Y

            if self.rect.y < self.target_y:
                self.rect.y = min(self.rect.y + self.game.MOVE_SPEED, self.target_y)
            elif self.rect.y > self.target_y:
                self.rect.y = max(self.rect.y - self.game.MOVE_SPEED, self.target_y)

        def draw(self, surface):
            pygame.draw.rect(surface, self.game.WHITE, self.rect)

    class Obstacle:
        def __init__(self, game, lane_type):
            self.game = game
            self.rect = pygame.Rect(game.width, 0, game.OBSTACLE_WIDTH, game.height // 2)
            self.rect.y = 0 if lane_type == "top" else game.height // 2
            self.scored = False

        def update(self):
            self.rect.x -= self.game.OBSTACLE_SPEED

        def draw(self, surface):
            pygame.draw.rect(surface, self.game.WHITE, self.rect)

        def is_off_screen(self):
            return self.rect.right < 0


# --- Tkinter App Class ---
class App:
    def __init__(self, game, width=600, height=600):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Cube Infinite Runner")

        self.root.geometry(f"{width}x{height}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.title_label = tk.Label(self.root, text="Cube Infinite Runner", 
                                    font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.label = tk.Label(self.root)
        self.label.pack()

        self.info_label = tk.Label(self.root, text="Press SPACE to jump | Press R to restart", 
                                   font=("Arial", 10))
        self.info_label.pack(pady=5)
        
        # Bind keyboard events
        self.root.bind("<KeyPress-space>", self.on_space_press)
        self.root.bind("<KeyRelease-space>", self.on_space_release)
        self.root.bind("<KeyPress-r>", self.on_r_press)
        self.root.bind("<KeyRelease-r>", self.on_r_release)
        
        # Make sure the window can receive focus
        self.root.focus_set()
        
        self.update_label()
        self.root.mainloop()

    def on_space_press(self, event):
        self.game.space_pressed = True

    def on_space_release(self, event):
        self.game.space_pressed = False

    def on_r_press(self, event):
        self.game.r_pressed = True

    def on_r_release(self, event):
        self.game.r_pressed = False

    def on_close(self):
        self.game.running = False
        self.root.destroy()

    def update_label(self):
        if self.game.screen is not None:
            raw_data = pygame.image.tobytes(self.game.screen, "RGB")
            image = Image.frombytes("RGB", (self.game.width, self.game.height), raw_data)
            image_tk = ImageTk.PhotoImage(image)

            self.label.config(image=image_tk)
            self.label.image = image_tk

        # Schedule next update
        self.root.after(1, self.update_label)


# --- Main ---
if __name__ == "__main__":
    game = InfiniteRunner(size=(800, 600), fps=60)
    game.start()  # Run Pygame in its own thread
    sleep(0.5)  # Give Pygame time to initialize
    app = App(game, width=850, height=700)