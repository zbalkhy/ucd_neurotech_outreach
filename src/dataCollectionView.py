import tkinter as tk
from tkinter import *
import numpy as np
from dataCollectionViewModel import dataCollectionViewModel
from eventClass import *

class dataCollectionView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: dataCollectionViewModel):
        super().__init__()

        #set up class variables
        self.frame: tk.Frame = frame
        self.view_model = view_model
        self.subscribe_to_subject(self.view_model.user_model)

        self.collect_stream_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.collect_stream_frame.pack(side="top", fill="both", expand=True)

        #create dropdown
        self.create_dropdown()

        self.trial_mod_frame = tk.Frame(frame, borderwidth = 1, relief = "solid")
        self.trial_mod_frame.pack(side = "top", fill = "both", expand=True)

        #saving the amount of trials into a stringvar
        self.trial_num_str = StringVar(self.trial_mod_frame)
        self.trial_num_str.set("Number of Trials: 0")

        #button to collect trial, locks the dropdown
        tk.Button(self.trial_mod_frame, text = "Collect Trial", width=6, height=1, command = self.collect_trial).pack(pady=10, padx=10, anchor = "e", side = LEFT)
        
        #button to clear trials, unlocks the dropdown
        tk.Button(self.trial_mod_frame, text = "Clear Trials", width=6, height=1, command = self.clear_trials).pack(pady=10, padx = 10, anchor = "e", side = LEFT)

        #label with the amount of trials
        self.trial_label = tk.Label(self.trial_mod_frame, textvariable=self.trial_num_str).pack(pady=10, padx=10, anchor="e", side = LEFT)

        self.save_dataset_frame = tk.Frame(frame, borderwidth=1, relief = "solid")
        self.save_dataset_frame.pack(side = "top", fill = "both", expand = True)

        #button to save dataset, unlocks the dropdown
        self.save_dataset_button = tk.Button(self.save_dataset_frame, text = "Save Dataset", width=6, height=1, command = self.save_dataset).pack(pady = 10, padx = 10, anchor = "e", side = RIGHT)
        
        #entry to save dataset name
        self.dataset_name = tk.StringVar(self.save_dataset_frame)
        self.dataset_name_entry = tk.Entry(self.save_dataset_frame, textvariable = self.dataset_name).pack(fill = X, side = "left", expand = True, padx = 10)

    def create_dropdown(self):
        for child in self.collect_stream_frame.winfo_children():
            child.destroy()

        streams = self.view_model.get_streams()
        self.stream_names = []
        for stream in streams:
            self.stream_names.append(stream.stream_name)
        self.collection_stream = StringVar(self.collect_stream_frame)
        self.collection_stream.set(self.stream_names[0])
        self.dropdown = OptionMenu(self.collect_stream_frame, self.collection_stream, *self.stream_names)
        self.dropdown.pack(anchor = 'nw', side = RIGHT, padx = 10)
        dropdown_label = tk.Label(self.collect_stream_frame, text="Stream:").pack(anchor='nw', side = LEFT, padx = 10, pady=5)
        
    def on_notify(self, eventData: any, event: EventType) -> None:
        if event == EventType.DEVICELISTUPDATE:
            self.create_dropdown()
        return
        
    def collect_trial(self) -> None:
        collection_stream = self.collection_stream.get()
        self.view_model.add_dataset(collection_stream)
        self.lock()

    def clear_trials(self) -> None:
        self.view_model.clear_dataset()
        self.lock()

    def lock(self) -> None:
        #locks and unlocks the dropdow as well as update the trial number label
        trial_number = self.view_model.get_trial_number()
        if trial_number == 0:
            self.dropdown.config(state="normal")
        elif trial_number > 0:
            self.dropdown.config(state="disabled")
        else:
            None
        self.trial_num_str.set("Number of Trials: " + str(trial_number))

    def save_dataset(self) -> None:
        name = self.dataset_name.get()
        self.dataset_name.set('')
        self.view_model.save_dataset(name)
        self.clear_trials()
        self.lock()
        return