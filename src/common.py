from tkinter import Frame, Label

# streaming
RETRY_SEC = 1.5

# user context
QUEUE_LENGTH = 100

# float the orb game
BLACK = (0,0,0)
WHITE = (255,255,255)
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
GRAVITY = 0.05
PYGAME_WINDOW_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

def create_grid(root, rows: int, cols: int, grid_names: list[list[str]]) -> list[list[Frame]]:
    # Make the grid expandable
    for i in range(rows):
        root.rowconfigure(i, weight=1)
    for j in range(cols):
        root.columnconfigure(j, weight=1)

    # Create frames dynamically
    frames = []
    for i in range(rows):
        row_frames = []
        for j in range(cols):
            frame = Frame(root, borderwidth=2, relief="solid")
            frame.grid(row=i, column=j, sticky="nsew", padx=5, pady=5)

            # Example content: label with coordinates
            label = Label(frame, text=grid_names[i][j], bg=frame["bg"])
            label.pack(expand=False, anchor="w", padx=5)

            row_frames.append(frame)
        frames.append(row_frames)
    return frames