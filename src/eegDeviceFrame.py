import tkinter as tk
import numpy as np
from threading import Thread, Lock
from eegDeviceViewModel import EEGDeviceViewModel
from eventClass import *

class EEGDeviceFrame(EventClass):
    def __init__(self, frame: tk.Frame, view_model: EEGDeviceViewModel):
        super().__init__()

        # set class variables
        self.frame: tk.Frame = frame
        self.data_thread: Thread = None
        self.view_model = view_model

        self.subscribe_to_subject(self.view_model.user_model)

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
        
        ## Input device name
        tk.Label(self.new_device_frame, text="Device Name").pack(anchor="w", padx=30)
        self.device_name_entry = tk.Entry(self.new_device_frame)
        self.device_name_entry.pack(anchor="w", padx=30)
        
        # Connect Button
        tk.Button(
            self.new_device_frame,
            text="Add Device",
            command=self.add_device,
            width=18,
        ).pack(pady=10, padx=30, anchor="w")
        
        # Create frame to hold the device list
        self.device_list_frame = tk.Frame(self.frame, borderwidth=1, relief="solid")
        self.device_list_frame.pack(side="top", fill="both", expand=True)
        self.pack_device_list()
        
    def on_notify(self, eventData: any, event: EventType ) -> None:
        if event == EventType.DEVICELISTUPDATE:
            self.pack_device_list()
        return
    
    def pack_device_list(self):
        for child in self.device_list_frame.winfo_children():
            child.destroy()

        # create a canvas and a scroll bar to pack in the frame.
        self.device_list_canvas = tk.Canvas(self.device_list_frame)
        self.device_list_scrollbar = tk.Scrollbar(self.device_list_frame, 
                                                  orient="vertical", 
                                                  command=self.device_list_canvas.yview)
        
        # create scrollable frame to hold device list
        self.scrollable_frame = tk.Frame(self.device_list_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.device_list_canvas.configure(
                scrollregion=self.device_list_canvas.bbox("all")
            )
        )

        self.device_list_canvas.create_window((0, 0), 
                                              window=self.scrollable_frame, 
                                              anchor="nw")
        self.device_list_canvas.configure(yscrollcommand=self.device_list_scrollbar.set)

        # pack canvas and scrollbar
        self.device_list_canvas.pack(side="left", fill="both", expand=True)
        self.device_list_scrollbar.pack(side="right", fill="y")

        # create a two column grid to hold 
        for i, device in enumerate(self.view_model.get_device_names()):
            print(self.view_model.get_device_names())
            label = tk.Label(self.scrollable_frame, text=device, anchor="w")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            button = tk.Button(self.scrollable_frame, text="Start Stream", 
                               command=lambda x=device: self.start_device_stream(x))
            button.grid(row=i, column=1, padx=5, pady=5, sticky="e")
        
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def start_device_stream(self, device_name: str) -> None:
        self.view_model.start_device_stream(device_name)

    def add_device(self) -> None:
        # potentially need to type check the port field to make sure we actually have an int
        # probably should do an error handler in general if the device failed to connect
        self.view_model.add_device(self.IP_entry.get(), 
                                   int(self.port_entry.get()), 
                                   self.device_name_entry.get())

