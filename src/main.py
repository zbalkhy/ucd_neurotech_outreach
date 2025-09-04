import tkinter as tk
from deviceConnector import DeviceConnector
from plotter import Plotter
from floatTheOrbGame import FloatTheOrb
from collections import deque
from common import RAW_DATA, QUEUE_LENGTH
from threading import Lock

frame_names = [[f"Device Connector", f"Visualizer"],[f"Float The Orb", f"Blank"]]

def create_grid(root, rows, cols):
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
            frame = tk.Frame(root, borderwidth=2, relief="solid")
            frame.grid(row=i, column=j, sticky="nsew", padx=5, pady=5)

            # Example content: label with coordinates
            label = tk.Label(frame, text=frame_names[i][j], bg=frame["bg"])
            label.pack(expand=False)

            row_frames.append(frame)
        frames.append(row_frames)
    return frames

if __name__ == "__main__":
    
    # initialize user context
    user_context = {RAW_DATA: deque(maxlen=QUEUE_LENGTH)}
    user_context_lock = Lock()
    
    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frames = create_grid(root,2,2)

    def on_closing():
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create device connector
    device_connector = DeviceConnector(frames[0][0], user_context, user_context_lock)

    # create plotter
    plotter = Plotter(frames[0][1], user_context)

    # create game
    float_the_orb = FloatTheOrb(frames[1][0], user_context, user_context_lock)    
    #float_the_orb.start_pygame()

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any future queued commands.
    root.mainloop()

