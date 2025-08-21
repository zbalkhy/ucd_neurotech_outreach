import tkinter as tk
#from collections import deque
import threading
import numpy as np
from threading import Lock
from time import sleep
from common import RAW_DATA

class DeviceConnector():
    def __init__(self, root: tk.Tk, user_context: dict, user_context_lock: Lock):
        # set root and frame for the tk window
        self.root = root
        self.frame = tk.Frame(self.root)
        self.user_context = user_context
        self.user_context_lock = user_context_lock
        self.data_thread = None
        
        # create a quit button
        self.button_sin = tk.Button(master=root, text="Generate sine", command=self.start_sin_thread)
        
        # place the button at the bottom of the window
        self.button_sin.pack(side=tk.BOTTOM)
    
    def _update_user_context(self, key, value):
        with self.user_context_lock:
            self.user_context[key] = value

    def make_sin(self, user_context):
        t=0
        while True:
            user_context[RAW_DATA].append(np.sin(0.01*np.pi*t))
            t+=1
            sleep(0.004)
    
    def start_sin_thread(self):
        if not self.data_thread:
            self.data_thread = threading.Thread(target=self.make_sin, 
                                        kwargs={'user_context': self.user_context})
            self.data_thread.start()

