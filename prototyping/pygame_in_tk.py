import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Headless Pygame

import tkinter as tk
import threading
import pygame
from PIL import Image, ImageTk
from time import sleep

# --- Pygame Class ---
class Game:
    def __init__(self,size,fps):
        self.width = size[0]
        self.height = size[1]
        self.fps = fps
        self.dt = 0
        self.screen = None
        self.pos = pygame.math.Vector2(size[0] // 2, size[1] // 2)
        self.vel = pygame.math.Vector2(0, 150)
        self.running = True
        self.clock = pygame.time.Clock()
        self.font = None

    def start(self):
        """Start the Pygame loop in a separate thread."""
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        """Pygame main loop."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.font = pygame.font.SysFont("Arial", 20)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.update()
            self.draw()
            pygame.display.flip()
            self.dt = self.clock.tick(self.fps) / 1000

    def update(self):
        """Update game logic."""
        self.pos += self.vel * self.dt
        if self.pos.y > self.height:
            self.pos.y = self.height
            self.vel.y *= -1
        if self.pos.y < 0:
            self.pos.y = 0
            self.vel.y *= -1

    def draw(self):
        """Draw objects/fps on the screen."""
        self.screen.fill("black")
        pygame.draw.circle(self.screen, "orange", self.pos, 16)

        fps = round(min(10000,self.clock.get_fps()))
        fps_text = self.font.render(f"FPS: {fps}", True, "white")
        self.screen.blit(fps_text, (10, 10))

# --- Tkinter App Class ---
class App:
    def __init__(self, game, width=500, height=500):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Pygame in Tkinter")

        self.root.geometry(f"{width}x{height}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.title_label = tk.Label(self.root, text="Bouncing Ball", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.label = tk.Label(self.root)
        self.label.pack()

        self.pos_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.pos_label.pack(pady=5)
        
        self.update_label()
        self.root.mainloop()

    def on_close(self):
        self.game.running = False
        self.root.destroy()

    def update_label(self):
        raw_data = pygame.image.tobytes(self.game.screen, "RGB")
        image = Image.frombytes("RGB", pygame.display.get_window_size(), raw_data)
        image_tk = ImageTk.PhotoImage(image)

        self.label.config(image=image_tk)
        self.label.image = image_tk 

        self.pos_label.config(text=f"Ball position: ({int(self.game.pos.x)}, {int(self.game.pos.y)})")

        # Schedule next update
        self.root.after(1, self.update_label)

# --- Main ---
if __name__ == "__main__":
    game = Game(size=(400,400), fps=60)
    game.start()  # Run Pygame in its own thread
    sleep(1)
    app = App(game, width=500, height=500)