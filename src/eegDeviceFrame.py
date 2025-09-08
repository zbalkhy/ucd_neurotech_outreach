import tkinter as tk
#from collections import deque
import numpy as np
from threading import Thread, Lock
from time import sleep
from common import RAW_DATA
from eegDeviceViewModel import EegDeviceViewModel

class EegDeviceFrame():
    def __init__(self, frame: tk.Frame, view_model: EegDeviceViewModel):
        
        # set class variables
        self.frame: tk.Frame = frame
        self.data_thread: Thread = None
        self.view_model = view_model

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
        
        # Current Devices Frame
        self.device_list_Frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.device_list_Frame.pack(side="top", fill="both", expand=True)
       
    
    def connect_device(self):
        # potentially need to type check the port field to make sure we actually have an int
        # probably should do an error handler in general if the device failed to connect
        self.view_model.connect_device(self.IP_entry.get(), int(self.port_entry.get()))

