import tkinter as tk
#from collections import deque
import threading
import numpy as np
from threading import Lock
from time import sleep
from common import RAW_DATA, RETRY_SEC, create_grid
import socket
import time
from deviceStreamer import DeviceStreamer

class EegDeviceFrame():
    def __init__(self, frame: tk.Tk, user_context: dict, user_context_lock: Lock):
        
        # set frame for the tk window
        self.frame = frame
        self.user_context = user_context
        self.user_context_lock = user_context_lock
        self.data_thread = None
        self.devices = []

        # New Device Frame
        self.new_device_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.new_device_frame.pack(side="top", fill="both", expand=True)
        
        ## Input device IP
        tk.Label(self.new_device_frame, text="DeviceIP").pack(anchor="w", padx=30)
        self.IP_entry = tk.Entry(self.new_device_frame)
        self.IP_entry.pack(anchor="w", padx=30)
        
        ## Input device port
        tk.Label(self.new_device_frame, text="Device Port").pack(anchor="w", padx=30)
        self.port_entry = tk.Entry(self.new_device_frame)
        self.port_entry.pack(anchor="w", padx=30)
        
        # Connect Button
        tk.Button(
            self.new_device_frame,
            text="Connect Device",
            command=self.connect_device,
            width=18,
        ).pack(pady=10, padx=30, anchor="w")
        
        # New Device Frame
        self.device_list_Frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.device_list_Frame.pack(side="top", fill="both", expand=True)
        # sine generator
        self.button_sin = tk.Button(master=self.device_list_Frame, 
                                    text="Generate sine", 
                                    command=self.start_sin_thread)
        
        # place the button at the bottom of the window
        self.button_sin.pack()
    
    def _update_user_context(self, key, value):
        with self.user_context_lock:
            self.user_context[key] = value

    def connect_device(self):
        IP_address = self.IP_entry.get()
        port = self.port_entry.get()
        print(IP_address)
        new_device = DeviceStreamer(IP_address, int(port), RETRY_SEC, self.user_context)  
        self.devices.append(new_device)
        new_device.stream_thread()

    def make_sin(self, user_context):
        t=0
        while True:
            user_context[RAW_DATA].append(15*np.sin(0.01*np.pi*t))
            t+=1
            sleep(0.004)
    
    def start_sin_thread(self):
        if not self.data_thread:
            self.data_thread = threading.Thread(target=self.make_sin, 
                                        kwargs={'user_context': self.user_context})
            self.data_thread.start()

