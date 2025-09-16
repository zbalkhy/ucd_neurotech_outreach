from eventClass import *
from featureViewModel import FeatureViewModel

import tkinter as tk
from tkinter import ttk
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
        self.cur_datasets: list[tk.StringVar] = []
        self.cur_feature: tk.StringVar = tk.StringVar()

        # set up and pack selection frame
        self.selection_frame: tk.Frame = tk.Frame(self.frame)
        self.selection_frame.pack(side="left", fill="both", expand=True)
        
        # Dropdown menus for the datasets  
        self.dataset_dropdowns: list[ttk.Combobox] = []
        self.add_dataset_dropdown()
        self.add_dataset_dropdown()

        # Dropdown for features
        self.add_feature_dropdown()

        # set up and pack plotter frame
        self.plotter_frame: tk.Frame = tk.Frame(self.frame)
        
        self.fig: Figure = Figure(figsize=(5, 4), dpi=100)
        # create a tk.DrawingArea.
        self.plot_canvas: FigureCanvasTkAgg  = FigureCanvasTkAgg(self.fig, master=self.plotter_frame)  
        
        # set up plotting
        self.plot_canvas.draw()
        self.plot_canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.plot_canvas.mpl_connect("key_press_event", key_press_handler)
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.plotter_frame.pack(side="right", fill="both", expand=True)

        self.update_plot(None)
    
    def add_dataset_dropdown(self) -> None:
        datasets = self.view_model.get_dataset_names()
        cur_dataset = tk.StringVar()
        cur_dataset.set(datasets[0])
        self.cur_datasets.append(cur_dataset)
        dropdown = ttk.Combobox(self.selection_frame, values=datasets, state="readonly")
        dropdown.config(textvariable=cur_dataset)
        dropdown.bind("<<ComboboxSelected>>", self.update_plot)
        dropdown.pack(pady=10)
        
        self.dataset_dropdowns.append(dropdown)

    def add_feature_dropdown(self) -> None:
        features = self.view_model.get_feature_names()
        self.cur_feature.set(features[0])
        dropdown = ttk.Combobox(self.selection_frame, values=features, state="readonly")
        dropdown.config(textvariable=self.cur_feature)
        dropdown.bind("<<ComboboxSelected>>", self.update_plot)
        dropdown.pack(pady=10)
    
        self.dataset_dropdowns.append(dropdown)

    def update_plot(self, event: tk.Event) -> None:
        if event:
            event.widget.selection_clear()
        self.fig.clear()
        feature = self.view_model.get_feature(self.cur_feature.get())
        datasets = [self.view_model.get_dataset(dataset.get()) for dataset in self.cur_datasets]

        feature_datasets = []
        for dataset in datasets:
            feature_dataset = []
            for i in range(dataset.shape[2]):
                trial = dataset[:,:,i]
                trial_feature = feature.apply(trial, 128)
                feature_dataset.append(trial_feature)
            feature_datasets.append(np.array(feature_dataset))
        
        # create an axis
        ax = self.fig.add_subplot(111)
        ax.set_title(f"Feature:{self.cur_feature.get()}")
        ax.set_ylabel("frequency")
        ax.set_xlabel("power")
        # plot data
        ax.hist(feature_datasets, bins=30, stacked=True, label=[ds.get() for ds in self.cur_datasets])
        ax.legend()
        # refresh canvas
        self.plot_canvas.draw()
        self.plot_canvas.flush_events()



    def on_notify(self, eventData: any, event: EventType):
        if event == EventType.DATASETUPDATE:
            # update all the dataset dropdowns when a new dataset comes in
            for opt, dropdown in self.dataset_dropdowns:
                dropdown.set_menu(opt, *self.view_model.get_dataset_names())
        