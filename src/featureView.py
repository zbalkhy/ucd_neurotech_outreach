from eventClass import *
from featureViewModel import FeatureViewModel

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
        
        self.cur_datasets: list[tk.StringVar] = []
        self.cur_feature: tk.StringVar = tk.StringVar()
        self.cur_channels: list[tk.IntVar] = []
        self.channel_dropdowns: list[ttk.Combobox] = []
        self.dataset_dropdowns: list[ttk.Combobox] = []

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
        
        # Dropdown for features
        self.feature_frame: tk.Frame = tk.Frame(self.selection_frame)
        self.feature_label = tk.Label(self.feature_frame, text="Feature")
        self.feature_label.pack()
        self.add_feature_dropdown()

        # Dropdown menus for the datasets  
        self.datasets_frame: tk.Frame = tk.Frame(self.selection_frame)

        self.dataset_label = tk.Label(self.datasets_frame, text="Datasets")
        self.dataset_label.pack()
        self.add_dataset_button = tk.Button(self.datasets_frame, 
                                            text="Add Dataset", 
                                            command=self.add_dataset_dropdown)
        self.add_dataset_button.pack()

        
        self.add_dataset_dropdown()

        self.datasets_frame.pack()
        self.feature_frame.pack()
        
    def add_dataset_dropdown(self) -> None:
        datasets = self.view_model.get_dataset_names()
        if not len(datasets):
            return
        cur_dataset = tk.StringVar()
        idx = min(len(self.dataset_dropdowns), len(datasets)-1) 
        cur_dataset.set(datasets[idx])
        self.cur_datasets.append(cur_dataset)

        dataset_frame = tk.Frame(self.datasets_frame)
        dataset_frame.pack()
        dataset_dropdown = ttk.Combobox(dataset_frame, values=datasets, state="readonly")
        dataset_dropdown.config(textvariable=cur_dataset)
        dataset_dropdown.bind("<<ComboboxSelected>>", self.update_plot)
        dataset_dropdown.pack(side='top', pady=10)

        channel_label = tk.Label(dataset_frame, text="Channel")
        channel_label.pack(padx=50)

        channels = list(range(self.view_model.get_dataset(cur_dataset.get()).shape[1]))
        cur_channel = tk.IntVar()
        cur_channel.set(0)
        self.cur_channels.append(cur_channel)
        channel_dropdown = ttk.Combobox(dataset_frame, values=channels, state="readonly")
        channel_dropdown.config(textvariable=cur_channel)
        channel_dropdown.bind("<<ComboboxSelected>>", self.update_plot)
        channel_dropdown.pack(side='top', pady=10, padx=10)
        
        self.dataset_dropdowns.append(dataset_dropdown)
        self.channel_dropdowns.append(channel_dropdown)
        self.update_plot(None)

    def add_feature_dropdown(self) -> None:
        features = self.view_model.get_feature_names()
        if len(features):
            self.cur_feature.set(features[0])
        dropdown = ttk.Combobox(self.feature_frame, values=features, state="readonly")
        dropdown.config(textvariable=self.cur_feature)
        dropdown.bind("<<ComboboxSelected>>", self.update_plot)
        dropdown.pack(side='top', pady=10)
    
        self.update_plot(None)

    def update_plot(self, event: tk.Event) -> None:
        # clear event and figure
        if event:
            event.widget.selection_clear()
        self.fig.clear()
        
        if len(self.cur_feature.get()) and len(self.cur_datasets):
            # calculate feature on dataset
            feature_datasets = self.view_model.calc_feature_datasets(
                self.cur_feature.get(), [dataset.get() for dataset in self.cur_datasets],
                [channel.get() for channel in self.cur_channels])
    
            # create an axis
            ax = self.fig.add_subplot(111)
            ax.set_title(f"Feature:{self.cur_feature.get()}")
            ax.set_ylabel("frequency")
            ax.set_xlabel("power")
            
            # plot data
            ax.hist(feature_datasets, bins=30, stacked=True, 
                    label=[ds.get() for ds in self.cur_datasets])
            ax.legend()
            
            # refresh canvas
            self.plot_canvas.draw()
            self.plot_canvas.flush_events()

    def on_notify(self, eventData: any, event: EventType):
        if event == EventType.DATASETUPDATE:
            # update all the dataset dropdowns when a new dataset comes in
            for opt, dropdown in self.dataset_dropdowns:
                dropdown.set_menu(opt, *self.view_model.get_dataset_names())
        