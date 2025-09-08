import tkinter as tk
from threading import Lock
from common import RAW_DATA, QUEUE_LENGTH
from collections import deque

class TkTemplate():
    def __init__(self, root: tk.Tk, user_context: dict, user_context_lock: Lock):
        # set root and frame for the tk window
        self.root = root
        self.frame = tk.Frame(self.root)
        self.user_context = user_context
        self.user_context_lock = user_context_lock
        
        # create a quit button
        self.button_quit = tk.Button(master=root, text="Quit", command=root.destroy)
        
        # place the button at the bottom of the window
        self.button_quit.pack(side=tk.BOTTOM)
    
    def _update_user_context(self, key, value):
        with self.user_context_lock:
            self.user_context[key] = value

if __name__ == "__main__":
    
    # initialize a tk root window
    root = tk.Tk()
    
    # name the window
    root.wm_title("")
    user_context = {RAW_DATA: deque(maxlen=QUEUE_LENGTH)}
    user_context_lock = Lock()
    # create template class
    app = TkTemplate(root)
    
    # start the main app loop
    root.mainloop()
   