import tkinter as tk
from eegDeviceFrame import EegDeviceFrame
from plotter import Plotter
from floatTheOrbGame import FloatTheOrb
from collections import deque
from common import RAW_DATA, QUEUE_LENGTH, create_grid, EVENTS
from threading import Lock
from eventClass import EventClass
from eventType import EventType


frame_names = [[f"Device Connector", f"Visualizer"],[f"Float The Orb", f"Data Collection"]]



if __name__ == "__main__":
    
    # initialize user context
    event_object = EventClass()
    user_context = {RAW_DATA: deque(maxlen=QUEUE_LENGTH), EVENTS: event_object}
    user_context_lock = Lock()
    
    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frames = create_grid(root,2,2, frame_names)

    def on_closing():
        event_object.notify(None, EventType.PROGRAMEXIT)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create device connector
    device_connector = EegDeviceFrame(frames[0][0], user_context, user_context_lock)

    # create plotter
    plotter = Plotter(frames[0][1], user_context)

    # create game
    float_the_orb = FloatTheOrb(frames[1][0], user_context, user_context_lock)    
    #float_the_orb.start_pygame()

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any future queued commands.
    root.mainloop()

