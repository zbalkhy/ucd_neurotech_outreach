import tkinter as tk
from plotter import Plotter

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_title("")
    plotter = Plotter(root)
    tk.mainloop()


