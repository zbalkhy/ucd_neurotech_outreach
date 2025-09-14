from eventClass import *
from featureViewModel import FeatureViewModel

import tkinter as tk
import numpy as np

# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure

class FeatureView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: FeatureViewModel):
        super().__init__()
        
         # set class variables
        self.frame: tk.Frame = frame
        self.view_model: FeatureViewModel = view_model
        self.subscribe_to_subject(self.view_model.user_model)

        # set up and pack toggle frame
        self.toggle_frame: tk.Frame = tk.Frame(self.frame)
        
        # feature 

        # set up and pack plotter frame
        self.plotter_frame: tk.Frame = tk.Frame(self.frame)
        
        self.fig: Figure = Figure(figsize=(5, 4), dpi=100)
        # create a tk.DrawingArea.
        self.plot_canvas: FigureCanvasTkAgg  = FigureCanvasTkAgg(self.fig, master=self.plotter_frame)  
        
        self.plot_canvas.draw()
        self.plot_canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.plot_canvas.mpl_connect("key_press_event", key_press_handler)
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.plotter_frame.pack(side="top", fill="both", expand=True)