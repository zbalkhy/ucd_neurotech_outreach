import tkinter as tk
from tkinter import *
from tkinter import ttk

from Classes.eventClass import *
from Models.classifierViewModel import ClassifierViewModel
from common import create_grid

class ClassifierView(EventClass):
    def __init__(self, frame: tk.Frame, view_model: ClassifierViewModel):
        super().__init__()

        self.frame: tk.Frame = frame
        self.view_model: ClassifierViewModel = view_model
        self.subscribe_to_subject(self.view_model.user_model)

        # State
        self.classifier_name = StringVar(self.frame)
        self.inner_frame = tk.Frame(self.frame)
        self.inner_frame.pack()
        self.grid_frames = create_grid(self.inner_frame, 1,2, None, True, False)

        # --- left panel: creation controls
        #self.create_frame = tk.Frame(frame, borderwidth=1, relief="solid")
        #self.create_frame.pack()

        # Name entry
        tk.Label(self.grid_frames[0][0], text="Classifier Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = tk.Entry(self.grid_frames[0][0], textvariable=self.classifier_name, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Label 0 dataset selector
        tk.Label(self.grid_frames[0][0], text="Label 0 Datasets:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.label0_listbox = tk.Listbox(self.grid_frames[0][0], selectmode=MULTIPLE, exportselection=False, height=5)
        self.label0_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        # Label 1 dataset selector
        tk.Label(self.grid_frames[0][0], text="Label 1 Datasets:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.label1_listbox = tk.Listbox(self.grid_frames[0][0], selectmode=MULTIPLE, exportselection=False, height=5)
        self.label1_listbox.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        # Feature selector
        tk.Label(self.grid_frames[0][1], text="Features:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.feature_listbox = tk.Listbox(self.grid_frames[0][1], selectmode=MULTIPLE, exportselection=False, height=5)
        self.feature_listbox.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        # Filter selector
        tk.Label(self.grid_frames[0][1], text="Filters:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.filter_listbox = tk.Listbox(self.grid_frames[0][1], selectmode=MULTIPLE, exportselection=False, height=5)
        self.filter_listbox.grid(row=4, column=1, padx=5, pady=5, sticky="we")
        
        # Create classifier button
        self.create_button = tk.Button(self.grid_frames[0][1], text="Create Classifier", bg="yellow",
                                       command=self.create_classifier)
        self.create_button.grid(row=6, column=0, columnspan=2, pady=10)

        self.refresh_lists()

    # -----------------------
    # UI Actions
    # -----------------------
    def refresh_lists(self):
        """Refresh dataset, feature, and filter listboxes from the UserModel."""
        self.label0_listbox.delete(0, END)
        self.label1_listbox.delete(0, END)
        self.feature_listbox.delete(0, END)
        self.filter_listbox.delete(0, END)

        datasets = list(self.view_model.user_model.get_datasets().keys())
        for ds in datasets:
            self.label0_listbox.insert(END, ds)
            self.label1_listbox.insert(END, ds)

        features = list(self.view_model.user_model.get_features().keys())
        for feat in features:
            self.feature_listbox.insert(END, feat)

        filters = list(self.view_model.user_model.filters.keys())
        for flt in filters:
            self.filter_listbox.insert(END, flt)

    def create_classifier(self):
        """Build a new classifier from selected items and save in the ViewModel."""
        name = self.classifier_name.get()
        if not name:
            return

        label0_idxs = self.label0_listbox.curselection()
        label1_idxs = self.label1_listbox.curselection()
        feature_idxs = self.feature_listbox.curselection()
        filter_idxs = self.filter_listbox.curselection()

        datasets0 = [self.label0_listbox.get(i) for i in label0_idxs]
        datasets1 = [self.label1_listbox.get(i) for i in label1_idxs]
        features = [self.feature_listbox.get(i) for i in feature_idxs]
        filters = [self.filter_listbox.get(i) for i in filter_idxs]

        self.view_model.create_classifier(name, datasets0, datasets1, features, filters)

        self.classifier_listbox.insert(END, name)
        self.classifier_name.set("")

    # -----------------------
    # Events
    # -----------------------
    def on_notify(self, eventData: any, event: EventType):
        if event in [EventType.DATASETUPDATE, EventType.STREAMUPDATE]:
            self.refresh_lists()
        
