import tkinter as tk
import numpy as np

# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from userModel import UserModel
from dataStream import StreamType

class Plotter():
    def __init__(self, frame: tk.Frame, user_model: UserModel):
        self.user_model = user_model
        self.frame = frame
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.continue_plotting = True

        # create a tk.DrawingArea.
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)  
        self.canvas.draw()

        # disable toolbar for now since we likeley wont 
        # pack_toolbar=False will make it easier to use a layout manager later on.
        #self.toolbar = NavigationToolbar2Tk(self.canvas, root, pack_toolbar=False)
        #self.toolbar.update()  
        
        self.canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)

        self.button_pause = tk.Button(master=frame, text="Play/Pause", command=self.play_pause)
        
        # Packing order is important. Widgets are processed sequentially and if there
        # is no space left, because the window is too small, they are not displayed.
        # The canvas is rather flexible in its size, so we pack it last which makes
        # sure the UI controls are displayed as long as possible.
        self.button_pause.pack(side=tk.BOTTOM)
        #self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.plot()
        return
        
    def play_pause(self):
        if not self.continue_plotting:
            self.continue_plotting = not self.continue_plotting
            self.plot()
        else:
            self.continue_plotting = not self.continue_plotting   

    def plot(self):
        ''' plot raw data '''

        # pull data from data queue
        # hard code software stream for now
        data = []
        for stream in self.user_model.get_streams():
            if stream.stream_type == StreamType.SOFTWARE:
                data = list(stream.get_stream())
                break
        # instead of ax.hold(False)
        self.fig.clear()

        # create an axis
        ax = self.fig.add_subplot(111)

        # plot data
        ax.plot(np.array(data))
        ax.set_ylim([-100,100])
        
        # refresh canvas
        self.canvas.draw()
        self.canvas.flush_events()
        if self.continue_plotting:
            self.frame.after(1, self.plot)