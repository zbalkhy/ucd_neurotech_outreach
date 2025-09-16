from tkinter import Frame, Label
import pandas as pd
import numpy as np

# streaming
RETRY_SEC = 1.5

# user context
QUEUE_LENGTH = 100
SAMPLING_FREQ = 250

# float the orb game
BLACK = (0,0,0)
WHITE = (255,255,255)
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
GRAVITY = 0.05
PYGAME_WINDOW_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# eeg bands
DELTA = [0.5,4]
THETA = [4,8]
ALPHA = [8,12]
BETA = [13-30]
GAMMA = [30, 45]

def split_dataset(dataset: pd.DataFrame, 
                  nsamples: int, ntrials: int) -> list[np.ndarray]:
    trials = np.zeros((nsamples, len(dataset.columns), ntrials))
    for i in range(ntrials):
        trials[:,:,i] = dataset[i*nsamples:i*nsamples + nsamples]
    return trials

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