"""Offscreen runner engine; input is read through a game-independent snapshot."""

import random
import threading

import pygame

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Classes.controllerState import KeyboardController


class InfiniteRunner:
    def __init__(self, size, fps, parent=None, user_model=None,
                 read_controller=None):
        self.width, self.height = size
        self.fps = fps
        self.screen = None
        self.font = None
        self.player = None
        self.obstacles = []
        self.score = 0
        self.game_over = False
        self.upper_lane = False
        self.paused = False
        self.error = None
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        self._restart_event = threading.Event()
        self._frame_lock = threading.Lock()
        self._frame = None
        self.keyboard = KeyboardController() if read_controller is None else None
        self.read_controller = read_controller or self.keyboard.read_state

        self.PLAYER_SIZE = 40
        self.PLAYER_X = 150
        self.MOVE_SPEED = 20
        self.OBSTACLE_WIDTH = 40
        self.OBSTACLE_SPEED = 1
        self.SPAWN_INTERVAL_MS = 7200
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.TOP_LANE_Y = self.height // 4 - self.PLAYER_SIZE // 2
        self.BOTTOM_LANE_Y = (3 * self.height) // 4 - self.PLAYER_SIZE // 2
        self.active_time_ms = 0
        self.last_spawn_time = 0

    def start(self):
        if self.thread is not None:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.thread is not None:
            self.thread.join()
        self.running = False

    def request_restart(self):
        self._restart_event.set()

    def read_frame(self):
        with self._frame_lock:
            return self._frame

    def run(self):
        try:
            # Tk displays the image; a second SDL window is unnecessary.
            pygame.font.init()
            self.screen = pygame.Surface((self.width, self.height))
            self.font = pygame.font.SysFont("consolas", 32)
            self.player = self.Player(self)
            clock = pygame.time.Clock()
            while not self._stop_event.is_set():
                elapsed_ms = clock.tick(self.fps)
                self.step(elapsed_ms)
                self.draw()
                frame = pygame.image.tobytes(self.screen, "RGB")
                with self._frame_lock:
                    self._frame = frame
        except Exception as error:
            self.error = str(error)
        finally:
            self.running = False

    def step(self, elapsed_ms):
        """Advance active game time only while the selected input is ready."""
        if self._restart_event.is_set():
            self._restart_event.clear()
            self.reset_game()
        state = self.read_controller()
        was_paused = self.paused
        self.paused = not state.ready
        if self.paused or self.game_over:
            return
        self.upper_lane = state.upper_lane
        # Exclude the interval that straddled an input recovery.
        if not was_paused:
            self.active_time_ms += elapsed_ms
        if self.active_time_ms - self.last_spawn_time >= self.SPAWN_INTERVAL_MS:
            lane = random.choice(["top", "bottom"])
            self.obstacles.append(self.Obstacle(self, lane))
            self.last_spawn_time = self.active_time_ms
        self.player.update()
        for obstacle in self.obstacles:
            obstacle.update()
            if self.player.rect.colliderect(obstacle.rect):
                self.game_over = True
            if not obstacle.scored and obstacle.rect.right < self.player.rect.left:
                obstacle.scored = True
                self.score += 1
        self.obstacles = [obstacle for obstacle in self.obstacles
                          if not obstacle.is_off_screen()]

    def reset_game(self):
        """Reset the game state."""
        self.player = self.Player(self)
        self.obstacles = []
        self.score = 0
        self.game_over = False
        self.active_time_ms = 0
        self.last_spawn_time = 0

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
        self.draw_text(f"Score: {self.score}",
                       self.width // 2, self.height - 30, center=True)

        if self.paused:
            self.draw_text("INPUT PAUSED", self.width // 2,
                           self.height // 2 - 70, center=True)

        # Draw game over text
        if self.game_over:
            self.draw_text("GAME OVER", self.width // 2,
                           self.height // 2 - 30, center=True)
            self.draw_text("Press R to Restart", self.width // 2,
                           self.height // 2 + 10, center=True)

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
            self.target_y = (self.game.TOP_LANE_Y if self.game.upper_lane
                             else self.game.BOTTOM_LANE_Y)

            if self.rect.y < self.target_y:
                self.rect.y = min(
                    self.rect.y + self.game.MOVE_SPEED, self.target_y)
            elif self.rect.y > self.target_y:
                self.rect.y = max(
                    self.rect.y - self.game.MOVE_SPEED, self.target_y)

        def draw(self, surface):
            pygame.draw.rect(surface, self.game.WHITE, self.rect)

    class Obstacle:
        def __init__(self, game, lane_type):
            self.game = game
            self.rect = pygame.Rect(
                game.width, 0, game.OBSTACLE_WIDTH, game.height // 2)
            self.rect.y = 0 if lane_type == "top" else game.height // 2
            self.scored = False

        def update(self):
            self.rect.x -= self.game.OBSTACLE_SPEED

        def draw(self, surface):
            pygame.draw.rect(surface, self.game.WHITE, self.rect)

        def is_off_screen(self):
            return self.rect.right < 0


if __name__ == "__main__":
    from Models.userModel import UserModel
    from View.runnerView import RunnerView
    from ViewModel.runnerViewModel import RunnerViewModel
    import tkinter as tk

    root = tk.Tk()
    RunnerView(root, RunnerViewModel(UserModel()))
    root.mainloop()
