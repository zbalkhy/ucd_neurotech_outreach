import tkinter as tk
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

frame_names = [[f"Inventory", f"Classifier", f"Visualizer"],
               [f"Data Collector", f"Filters Maker", f"Feature Viewer"]]

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

if __name__ == "__main__":
    
    # initialize user model
    user_model = UserModel()
    data = loadmat('/Users/zacariabalkhy/ucd_neurotech_outreach/src/data.mat')
    for key in data.keys():
        if key in ['eyesOpen', 'eyesClosed']:
            user_model.add_dataset(key, data[key])

    streams = resolve_streams()

    if len(streams):
        openBCIStream = LslStream(streams[0], 250, "openbci", StreamType.DEVICE, 250)
        user_model.add_stream(openBCIStream)

    data_stream = SoftwareStream("streamtest", StreamType.SOFTWARE, 300)
    user_model.add_stream(data_stream)
    
    # add default features to the user model
    for type in FeatureType:
        if type != FeatureType.CUSTOM:
            user_model.add_feature(FeatureClass(type))

    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frames = create_grid(root,2,3, frame_names)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create device connector
    #device_frame_viewmodel = EEGDeviceViewModel(user_model)
    #device_connector = EEGDeviceView(frames[0][0], device_frame_viewmodel)

    # create inventory
    inventory_viewmodel = InventoryViewModel(user_model)
    inventory_view = InventoryView(frames[0][0], inventory_viewmodel)

    # create classifier
    classifier_view_model = ClassifierViewModel(user_model)
    classifier_view = ClassifierView(frames[0][1], classifier_view_model)

    # create plotter
    plotter_view_model, plotter_view = create_plotter(frames[0][2], user_model) 
    

    # create feature viewer
    feature_view_model = FeatureViewModel(user_model)
    feature_view = FeatureView(frames[1][2], feature_view_model)

    #create filter frame
    filter_frame_viewmodel = filterViewModel(user_model)
    filter_module = filterView(frames[1][1], filter_frame_viewmodel)

    #create data collection frame
    dataCollection_frame_viewmodel = dataCollectionViewModel(user_model)
    dataCollection_module = dataCollectionView(frames[1][0], dataCollection_frame_viewmodel)

    # create game
    #float_the_orb = FloatTheOrb(frames[1][0], user_context, user_context_lock)    
    #float_the_orb.start_pygame()

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any future queued commands.
    root.mainloop()

