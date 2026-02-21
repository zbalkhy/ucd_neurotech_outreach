import tkinter as tk
from tkinter import *
import numpy as np
from ViewModel.dataCollectionViewModel import dataCollectionViewModel
from Classes.eventClass import *


class dataCollectionView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: dataCollectionViewModel):
        super().__init__()

        # set up class variables
        self.frame: tk.Frame = frame
        self.view_model = view_model
        self.subscribe_to_subject(self.view_model.user_model)

        self.collect_stream_frame = tk.Frame(
            frame, borderwidth=1, relief="solid")
        self.collect_stream_frame.pack(side="top", fill="both", expand=True)
        # bind key to frame and collect trial for each key press
        self.frame.bind("<Key>", self.collect_trial)

        # create dropdown
        self.create_dropdown()

        self.trial_mod_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        self.trial_mod_frame.pack(side="top", fill="both", expand=True)

        # saving the amount of trials into a stringvar
        self.trial_num_str = StringVar(self.trial_mod_frame)
        self.trial_num_str.set("trial#: 0")

        # saving the labeling of the keys into a stringvar
        self.key_labels = StringVar(self.trial_mod_frame)
        self.key_labels.set("")

        # button to start collecting trial
        tk.Button(
    self.trial_mod_frame,
    text="Start Collection",
    width=15,
    height=1,
    command=self.start_collection).pack(
        pady=10,
         padx=10)

        # button to clear trials, unlocks the dropdown
        tk.Button(
    self.trial_mod_frame,
    text="Clear Trials",
    width=15,
    height=1,
    command=self.clear_trials).pack(
        pady=10,
         padx=10)
        
        # button to collect trial, locks the dropdown
        tk.Button(self.trial_mod_frame, text="Collect Trial", width=6,
                  height=1, command=self.collect_trial).pack(pady=10, padx=10)

        # button to clear trials, unlocks the dropdown
        tk.Button(self.trial_mod_frame, text="Clear Trials", width=6,
                  height=1, command=self.clear_trials).pack(pady=10, padx=10)

        # label with the amount of trials
        self.trial_label = tk.Label(
            self.trial_mod_frame,
            textvariable=self.trial_num_str).pack(
            pady=10,
            padx=10)

        # label with the labeling of keys
        self.trial_label = tk.Label(
    self.trial_mod_frame,
    textvariable=self.key_labels).pack(
        pady=10,
         padx=10)

        self.save_dataset_frame = tk.Frame(
    frame, borderwidth=1, relief="solid")
        self.save_dataset_frame.pack(side="top", fill="both", expand=True)
        self.save_dataset_frame = tk.Frame(
            frame, borderwidth=1, relief="solid")
        self.save_dataset_frame.pack(side="top", fill="both", expand=True)

        # entry to save dataset name
        self.dataset_name = tk.StringVar(self.save_dataset_frame)
        self.dataset_name_entry = tk.Entry(
            self.save_dataset_frame,
            textvariable=self.dataset_name).pack(
            expand=True,
            padx=10)

        # button to save dataset, unlocks the dropdown
        self.save_dataset_button = tk.Button(
            self.save_dataset_frame,
            text="Save Dataset",
            width=6,
            height=1,
            command=self.save_dataset).pack(
            pady=10,
            padx=10)

        # button to save dataset, unlocks the dropdown
        self.save_dataset_button = tk.Button(
    self.save_dataset_frame,
    text="Save Dataset",
    width=15,
    height=1,
    command=self.save_dataset).pack(
        pady=10,
         padx=10)

    def start_collection(self) -> None:
        self.view_model.start_collecting()
        self.frame.focus_set()
        self.lock()
    
    def create_dropdown(self):
        for child in self.collect_stream_frame.winfo_children():
            child.destroy()

        streams = self.view_model.get_streams()
        self.stream_names = []
        for stream in streams:
            self.stream_names.append(stream.stream_name)
        self.collection_stream = StringVar(self.collect_stream_frame)
        self.collection_stream.set(self.stream_names[0])
        self.dropdown = OptionMenu(
            self.collect_stream_frame,
            self.collection_stream,
            *self.stream_names)
        self.dropdown.pack(anchor='nw', side=RIGHT, padx=10)
        dropdown_label = tk.Label(
            self.collect_stream_frame, text="Stream:").pack(
            anchor='nw', side=LEFT, padx=10, pady=5)

    def on_notify(self, eventData: any, event: EventType) -> None:
        if event == EventType.STREAMUPDATE:
            self.create_dropdown()
        return
        
    def collect_trial(self, event) -> None:
        if self.view_model.collecting:
            #only collects if is currently in collecting mode
            collection_stream = self.collection_stream.get()
            if event.char.isalpha():
                #only collects alphabet keys
                self.view_model.add_dataset(collection_stream, event.char)
            self.lock()

    def clear_trials(self) -> None:
        self.view_model.clear_dataset()
        self.lock()

    def lock(self) -> None:
        # locks and unlocks the dropdow as well as update the trial number
        # label
        trial_number = self.view_model.get_trial_number()
        if trial_number == 0:
            self.dropdown.config(state="normal")
        elif trial_number > 0:
            self.dropdown.config(state="disabled")
        else:
            None
        self.trial_num_str.set("trial# " + str(trial_number))
        try:
            unique_labels = self.view_model.get_unique_labels()
            key_label_str = ''
            for idx, value in enumerate(unique_labels):
                key_label_str = key_label_str + value + ': ' + str(idx) + '\n'
            self.key_labels.set(key_label_str)
        except:
            self.key_labels.set("")

    def save_dataset(self) -> None:
        name = self.dataset_name.get()
        self.dataset_name.set('')
        self.view_model.save_dataset(name)
        self.clear_trials()
        self.lock()
        return
