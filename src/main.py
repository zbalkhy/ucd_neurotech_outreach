import tkinter as tk
from tkinter import ttk
from plotterView import PlotterView, create_plotter
from plotterViewModel import PlotterViewModel
from floatTheOrbGame import FloatTheOrb
from common import create_grid
from userModel import UserModel
from eegDeviceView import EEGDeviceView
from eegDeviceViewModel import EEGDeviceViewModel
from inventoryView import InventoryView
from inventoryViewModel import InventoryViewModel
from dataStream import DataStream, StreamType
from softwareStream import SoftwareStream
from composedStream import ComposedStream
from filterViewModel import filterViewModel
from filterView import filterView
from dataCollectionViewModel import dataCollectionViewModel
from dataCollectionView import dataCollectionView
from classifierView import ClassifierView
from classifierViewModel import ClassifierViewModel
from featureView import FeatureView
from featureViewModel import FeatureViewModel
from featureClass import FeatureClass, FeatureType
import pandas as pd
import numpy as np
from lslStream import LslStream
from xrpControlStream import XRPControlStream
from scipy.io import loadmat
from pylsl import StreamInlet, resolve_streams

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
    
    root.destroy()

def open_feature_viewer(root, view_model):
    t = tk.Toplevel(root)
    t.wm_title('Feature Viewer')
    feature_view = FeatureView(t, feature_view_model)



if __name__ == "__main__":
    print("main app starting")
    # initialize user model
    user_model = UserModel()
    #Change back to ./data.mat
    #data = loadmat('./data.mat')
    #for key in data.keys():
    #    if key in ['eyesOpen', 'eyesClosed']:
    #        user_model.add_dataset(key, data[key])

    # streams = resolve_streams()

    # if len(streams):
    #     openBCIStream = LslStream(streams[0], 250, "openbci", StreamType.DEVICE, 250)
    #     user_model.add_stream(openBCIStream)

    data_stream = SoftwareStream("streamtest", StreamType.SOFTWARE, 300)
    user_model.add_stream(data_stream)

    data_stream2 = SoftwareStream("streamtest2", StreamType.SOFTWARE, 1000)
    user_model.add_stream(data_stream2)

    
    # add default features to the user model
    for type in FeatureType:
        if type != FeatureType.CUSTOM:
            user_model.add_feature(FeatureClass(type))

    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    
    # create paned window for each row, this allows them to be adjustable
    inner_paned_window = ttk.PanedWindow(root, orient="vertical")
    inner_paned_window.pack(side = "top", fill = "both", expand=True)
    
    # create top and bottom panes
    top_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    bottom_pane = tk.Frame(inner_paned_window, borderwidth=2, relief="solid")
    inner_paned_window.add(top_pane)
    inner_paned_window.add(bottom_pane)
    
    # create a gride in each pane to hold our widgets
    top_grid_frames = create_grid(top_pane,1,2, top_grid_names,resize=True)
    bottom_grid_frames = create_grid(bottom_pane,1,3, bottom_grid_names)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    #create data collection frame
    dataCollection_frame_viewmodel = dataCollectionViewModel(user_model)
    dataCollection_module = dataCollectionView(bottom_grid_frames[0][0], dataCollection_frame_viewmodel)

    #create filter frame
    filter_frame_viewmodel = filterViewModel(user_model)
    filter_module = filterView(bottom_grid_frames[0][1], filter_frame_viewmodel)

    # create classifier
    classifier_view_model = ClassifierViewModel(user_model)
    classifier_view = ClassifierView(bottom_grid_frames[0][2], classifier_view_model)
    
    # create inventory
    inventory_viewmodel = InventoryViewModel(user_model)
    inventory_view = InventoryView(top_grid_frames[0][0], inventory_viewmodel)

    # create plotter
    plotter_view_model, plotter_view = create_plotter(top_grid_frames[0][1], user_model)    
    
    
    # create feature viewer
    feature_view_model = FeatureViewModel(user_model)

    # create menu bar
    menubar = tk.Menu(root)
    actions = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Actions", menu=actions)
    actions.add_command(label='Open Feature Viewer', command=lambda: open_feature_viewer(root, feature_view_model))
    root.config(menu=menubar)
    


    # create game
    #float_the_orb = FloatTheOrb(frames[1][0], user_context, user_context_lock)    
    #float_the_orb.start_pygame()

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any future queued commands.
    root.mainloop()

