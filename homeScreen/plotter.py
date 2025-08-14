import tkinter as tk
import numpy as np
from collections import deque
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from editor import Editor

class Plotter():
    def __init__(self, root):
        self.root = root
        self.frame = tk.Frame(self.root)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.t = 0
        self.length = 100
        self.data_chunk = deque()
        self.continue_plotting = True
        self.editor = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)  # A tk.DrawingArea.
        self.canvas.draw()

        # pack_toolbar=False will make it easier to use a layout manager later on.
        self.toolbar = NavigationToolbar2Tk(self.canvas, root, pack_toolbar=False)
        self.toolbar.update()  
        self.canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)

        self.button_quit = tk.Button(master=root, text="Quit", command=root.destroy)
        self.button_pause = tk.Button(master=root, text="Play/Pause", command=self.play_pause)
        self.button_editor = tk.Button(master=root, text="Open Editor", command=self.open_editor)
        
        # Packing order is important. Widgets are processed sequentially and if there
        # is no space left, because the window is too small, they are not displayed.
        # The canvas is rather flexible in its size, so we pack it last which makes
        # sure the UI controls are displayed as long as possible.
        self.button_quit.pack(side=tk.BOTTOM)
        self.button_pause.pack(side=tk.BOTTOM)
        self.button_editor.pack(side=tk.BOTTOM)
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.plot()
        return
    
    def open_editor(self):
        self.editor_window = tk.Toplevel(self.root)
        self.editor_window.geometry('500x500')

        self.editor = Editor(self.editor_window)
        
    def play_pause(self):
        if not self.continue_plotting:
            self.continue_plotting = not self.continue_plotting
            self.plot()
        else:
            self.continue_plotting = not self.continue_plotting   

    def plot(self):
        ''' plot some stuff '''
        self.t += 1

        if self.editor != None and "plot_fun" in self.editor.functions.keys():
            self.data_chunk.append(self.editor.functions["plot_fun"](self.t))
        else:
            self.data_chunk.append(np.sin(0.01*np.pi*self.t))
        
        if len(self.data_chunk) > self.length:
            self.data_chunk.popleft()
        # instead of ax.hold(False)
        self.fig.clear()

        # create an axis
        ax = self.fig.add_subplot(111)

        # plot data
        ax.plot(np.array(self.data_chunk))
        ax.set_ylim([-1,1])
        # refresh canvas
        self.canvas.draw()
        self.canvas.flush_events()
        if self.continue_plotting:
            self.root.after(0, self.plot)