import tkinter as tk
from tkinter import ttk
from View.plotterView import PlotterView, create_plotter
from ViewModel.plotterViewModel import PlotterViewModel
from Game.week1_game import InfiniteRunner, App
from common import create_grid, resource_path, MODAL_WIDGET_TITLE, ALPHA
from Models.userModel import UserModel
from Models.saveModel import SaveModel
from View.eegDeviceView import EEGDeviceView
from ViewModel.eegDeviceViewModel import EEGDeviceViewModel
from View.inventoryView import InventoryView
from ViewModel.inventoryViewModel import InventoryViewModel
from Stream.dataStream import DataStream, StreamType
from Stream.softwareStream import SoftwareStream
from Stream.composedStream import ComposedStream
from ViewModel.filterViewModel import filterViewModel
from View.filterView import filterView
from ViewModel.dataCollectionViewModel import dataCollectionViewModel
from View.dataCollectionView import dataCollectionView
from View.classifierView import ClassifierView
from ViewModel.classifierViewModel import ClassifierViewModel
from View.featureView import FeatureView
from ViewModel.featureViewModel import FeatureViewModel
from View.modalView import TextEntryModalView
from Classes.featureClass import FeatureClass, FeatureType
from Classes.editorClass import EditorClass
import pandas as pd
import numpy as np
from Stream.xrpControlStream import XRPControlStream
from scipy.io import loadmat

# Change to activate different UI based on session
# Currently switches between 0 and 1
# 0 = Default
# 1 = Plotter UI for Session 1
# 2 = Plotter UI for Session 2
SESSION_ID = 1


top_grid_names = [[f"Inventory", 'Visualizer']]
bottom_grid_names = [[f"Data Collector", f"Filter Maker", f"Classifier"]]


def on_closing():
    # Stop the plotter thread
    plotter_view.stop()
    # send shutdown event to each stream thread
    for data_stream in user_model.get_streams():
        data_stream.shutdown_event.set()

    # wait for each thread to exit before shutdown
    for data_stream in user_model.get_streams():
        if data_stream.is_alive():
            data_stream.join()
    save_model.dump(user_model)
    print("Saved User")
    root.destroy()


def open_feature_viewer(root, view_model):
    t = tk.Toplevel(root)
    t.wm_title('Feature Viewer')
    feature_view = FeatureView(t, feature_view_model)


def open_function_editor(root, user_model):
    t = tk.Toplevel(root)
    t.wm_title('Function Editor')
    editor = EditorClass(t)
    editor.add_observer(user_model)


def open_text_entry_modal(root):
    """Open the app's reusable text-entry modal."""
    TextEntryModalView(
        root,
        title=MODAL_WIDGET_TITLE,
        on_submit=lambda value: print(f"Modal entry submitted: {value}"))


def open_game(root, user_model):
    t = tk.Toplevel(root)
    t.wm_title('EEG RUNNNER')
    game = InfiniteRunner(
        size=(800, 600),
        fps=80,
        parent=t,
        user_model=user_model)
    game.start()
    game_ui = App(game, width=800, height=700, parent_window=t)
    t.protocol("WM_DELETE_WINDOW", game_ui.on_close)


if __name__ == "__main__":
    print("main app starting")
    # initialize user model
    save_model = SaveModel()
    user_model = save_model.load() if save_model.save_exists() else UserModel()
    user_model.add_observer(save_model)

    data_stream = SoftwareStream("eeg stream", StreamType.SOFTWARE, 250)
    user_model.add_stream(data_stream)

    # add default features to the user model
    for type in FeatureType:
        if type != FeatureType.CUSTOM:
            user_model.add_feature(FeatureClass(type))
    
    # temp load gold standard data.mat
    if SESSION_ID >= 2:
        data = loadmat(resource_path("data.mat"))
        for key in data.keys():
            if key in ['eyesOpen', 'eyesClosed']:
                user_model.add_dataset(key, data[key])
    
    # make alpha filter stream
    if SESSION_ID <= 2:
        user_model.add_filter("alpha", "bandpass", 4, ALPHA)
        filter_obj = user_model.get_filter("alpha")
        filtered_stream = ComposedStream(user_model.get_stream(
            "eeg stream"), [filter_obj], "alpha eeg stream", StreamType.FILTER, 250)
        user_model.add_stream(filtered_stream)

    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    try:
        root.state('zoomed')  # make the window take up the whole screen
    except tk.TclError:
        # probably on a linux system
        # root.attributes('-zoomed', True)
        print(Exception)

    # create paned window for each row, this allows them to be adjustable
    inner_paned_window = ttk.PanedWindow(root, orient="vertical")
    inner_paned_window.pack(side="top", fill="both", expand=True)

    # create top and bottom panes
    top_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    bottom_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    inner_paned_window.add(top_pane)
    inner_paned_window.add(bottom_pane)

    # create a gride in each pane to hold our widgets
    top_grid_frames = create_grid(top_pane, 1, 2, top_grid_names)
    bottom_grid_frames = create_grid(bottom_pane, 1, 3, bottom_grid_names)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create data collection frame
    dataCollection_frame_viewmodel = dataCollectionViewModel(user_model)
    dataCollection_module = dataCollectionView(
        bottom_grid_frames[0][0],
        dataCollection_frame_viewmodel,
        session_id=SESSION_ID)

    # create filter frame
    filter_frame_viewmodel = filterViewModel(user_model)
    filter_module = filterView(
        bottom_grid_frames[0][1],
        filter_frame_viewmodel,
        session_id=SESSION_ID)

    # create classifier
    classifier_view_model = ClassifierViewModel(user_model)
    classifier_view = ClassifierView(
        bottom_grid_frames[0][2],
        classifier_view_model,
        session_id=SESSION_ID)

    # create inventory
    inventory_viewmodel = InventoryViewModel(user_model)
    inventory_view = InventoryView(top_grid_frames[0][0], inventory_viewmodel)

    # create plotter
    plotter_view_model, plotter_view = create_plotter(
        top_grid_frames[0][1],
        user_model,
        session_id=SESSION_ID
    )

    # create feature viewer
    feature_view_model = FeatureViewModel(user_model)

    # create menu bar
    menubar = tk.Menu(root)
    actions = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Actions", menu=actions)
    actions.add_command(
        label='Open Feature Viewer',
        command=lambda: open_feature_viewer(
            root,
            feature_view_model))
    root.config(menu=menubar)
    actions.add_command(
        label='Open Code Editor',
        command=lambda: open_function_editor(root, user_model))
    actions.add_command(
        label='Play EEG RUNNER',
        command=lambda: open_game(root, user_model))
    actions.add_command(
        label='Connect EEG Device',
        command=lambda: open_text_entry_modal(root))

    # Show the modal once when this application session first starts.
    root.after(0, lambda: open_text_entry_modal(root))

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any
    # future queued commands.
    root.mainloop()
