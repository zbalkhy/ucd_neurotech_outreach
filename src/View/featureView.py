from Classes.eventClass import *
from src.ViewModel.featureViewModel import FeatureViewModel

import tkinter as tk
from tkinter import ttk

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
        self.dataset_list: tk.Listbox = None
        self.feature_list: tk.Listbox = None
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

        # set up and pack selection frame
        self.selection_frame: tk.Frame = tk.Frame(self.frame)
        self.selection_frame.pack(side="left", fill="both", expand=True)
        
        # select box  for features
        self.feature_label = tk.Label(self.selection_frame, text="Feature")
        self.feature_label.grid(row=1, column=0)
        self.add_feature_listbox()

        # Dropdown menus for the datasets  
        self.dataset_label = tk.Label(self.selection_frame, text="Datasets")
        self.dataset_label.grid(row=0, column=0)
        self.add_dataset_listbox()

        self.update_plot(None)

        
    def add_channel_listbox(self) -> None:
        self.dataset_list = tk.Listbox(self.selection_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        self.dataset_list.bind('<<ListboxSelect>>', self.update_plot)
        self.dataset_list.grid(row=1, column=1)

        datasets = self.view_model.get_dataset_names()
        for ds in datasets:
            self.dataset_list.insert(tk.END, ds)

    def add_dataset_listbox(self) -> None:
        self.dataset_list = tk.Listbox(self.selection_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        self.dataset_list.bind('<<ListboxSelect>>', self.update_plot)
        self.dataset_list.grid(row=0, column=1)

        datasets = self.view_model.get_dataset_names()
        for ds in datasets:
            self.dataset_list.insert(tk.END, ds)

    def add_feature_listbox(self) -> None:
        features = self.view_model.get_feature_names()
        self.feature_list = tk.Listbox(self.selection_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        self.feature_list.bind('<<ListboxSelect>>', self.update_plot)
        self.feature_list.grid(row=1, column=1)

        features = list(self.view_model.user_model.get_features().keys())
        for feat in features:
            self.feature_list.insert(tk.END, feat)

    def update_plot(self, event: tk.Event) -> None:
        self.fig.clear()
        
        cur_features = self.feature_list.curselection()
        cur_datasets = self.dataset_list.curselection()
        if len(cur_features) and len(cur_datasets):
            # calculate feature on dataset
            labels, feature_datasets = self.view_model.calc_feature_datasets(
                [self.feature_list.get(i) for i in cur_features], 
                [self.dataset_list.get(i) for i in cur_datasets],
                [])
    
            # create an axis
            ax = self.fig.add_subplot(111)
            ax.set_title(f"Feature")
            ax.set_ylabel("frequency")
            ax.set_xlabel("power")
            
            # plot data
            ax.hist(feature_datasets, bins=30, stacked=True, 
                    label=labels)
            ax.legend()
            
            # refresh canvas
        self.plot_canvas.draw()
        self.plot_canvas.flush_events()

    def refresh_datasets(self):
        self.dataset_list.delete(0, tk.END)
        datasets = self.view_model.get_dataset_names()
        for ds in datasets:
            self.dataset_list.insert(tk.END, ds)
    
    def on_notify(self, eventData: any, event: EventType):
        if event == EventType.DATASETUPDATE:
            # update all the dataset dropdowns when a new dataset comes in
            self.refresh_datasets()
        