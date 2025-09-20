import tkinter as tk
from plotter import Plotter
from floatTheOrbGame import FloatTheOrb
from common import create_grid
from userModel import UserModel
from eegDeviceView import EEGDeviceView
from eegDeviceViewModel import EEGDeviceViewModel
from dataStream import DataStream, StreamType
from softwareStream import SoftwareStream
from composedStream import ComposedStream
from filterViewModel import filterViewModel
from filterView import filterView
from dataCollectionViewModel import dataCollectionViewModel
from dataCollectionView import dataCollectionView
from featureView import FeatureView
from featureViewModel import FeatureViewModel
from featureClass import *
import pandas as pd
import numpy as np
from lslStream import LslStream


from pylsl import StreamInlet, resolve_streams

frame_names = [[f"Device Connector", f"Classifier", f"Visualizer"],
               [f"Float The Orb", f"Filters", f"Feature Viewer"]]

def on_closing():
    # send shutdown event to each stream thread
    for data_stream in user_model.get_streams():
        data_stream.shutdown_event.set()
    
    # wait for each thread to exit before shutdown
    for data_stream in user_model.get_streams():
        if data_stream.is_alive():
            data_stream.join()
    
    root.destroy()

if __name__ == "__main__":
    
    streams = resolve_streams()
    print(streams)

    openBCIStream = LslStream(streams[1], 250, "openbci", StreamType.DEVICE)
        

    # initialize user model
    user_model = UserModel()
    data_stream = SoftwareStream("software_stream_test", StreamType.SOFTWARE)
    user_model.add_stream(data_stream)
    user_model.add_stream(openBCIStream)

    #filtering = filterViewModel(user_model)
    #filtering.add_filter('lowpass', 4, [30])
    #filtering.add_filter('highpass', 4, [10])
    #filtering.add_filter('bandstop', 4, [20, 25])
    #filtering.remove_filter(1)

    #filtering.create_filter_stream("software_stream_test")

    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frames = create_grid(root,2,3, frame_names)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create device connector
    device_frame_viewmodel = EEGDeviceViewModel(user_model)
    device_connector = EEGDeviceView(frames[0][0], device_frame_viewmodel)

    # create plotter
    plotter = Plotter(frames[0][2], user_model)

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

