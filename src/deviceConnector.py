import tkinter as tk
#from collections import deque
import threading
import numpy as np
from threading import Lock
from time import sleep
from common import RAW_DATA
import socket
import time

class DeviceConnector():
    def __init__(self, frame: tk.Tk, user_context: dict, user_context_lock: Lock):
        # set frame for the tk window
        self.frame = frame
        self.user_context = user_context
        self.user_context_lock = user_context_lock
        self.data_thread = None
        
        # Create an input box (Entry widget)
        self.entry = tk.Entry(self.frame)
        self.entry.pack(expand=True, pady=10)

        # Create a submit button
        self.submit_button = tk.Button(self.frame, text="Submit", command=self.submit_action)
        self.submit_button.pack(pady=5)

        # Label to display result
        self.label = tk.Label(self.frame, text="")
        self.label.pack(pady=10)
        
        # create a quit button
        self.button_sin = tk.Button(master=self.frame, text="Generate sine", command=self.start_sin_thread)
        
        # place the button at the bottom of the window
        self.button_sin.pack(side=tk.BOTTOM)
    
    def _update_user_context(self, key, value):
        with self.user_context_lock:
            self.user_context[key] = value


    def submit_action(self):
        user_input = self.entry.get()  # get text from input box
        print("You entered:", user_input)  # do something with it
        self.label.config(text=f"You entered: {user_input}")  # update label

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

