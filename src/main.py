import tkinter as tk
from deviceConnector import DeviceConnector
from plotter import Plotter
from collections import deque
from common import RAW_DATA, QUEUE_LENGTH
from threading import Lock


if __name__ == "__main__":
    
    # initialize user context
    user_context = {RAW_DATA: deque(maxlen=QUEUE_LENGTH)}
    user_context_lock = Lock()
    
    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frame = tk.Frame(root)

    # create device connector
    device_connector_window = tk.Toplevel(root)
    device_connector_window.geometry('200x50')
    device_connector_window.wm_title("device connector")
    device_connector = DeviceConnector(device_connector_window, user_context, user_context_lock)

    # create plotter
    plotter_window = tk.Toplevel(root)
    plotter_window.wm_title("plotter")
    plotter = Plotter(plotter_window, user_context)

    root.mainloop()

