import tkinter as tk
from plotter import Plotter
from floatTheOrbGame import FloatTheOrb
from common import create_grid
from userModel import UserModel
from eegDeviceFrame import EEGDeviceFrame
from eegDeviceViewModel import EEGDeviceViewModel
from dataStream import DataStream, StreamType
from softwareStream import SoftwareStream

frame_names = [[f"Device Connector", f"Visualizer"],[f"Float The Orb", f"Experiment"]]

def on_closing():
    # send shutdown event to each stream thread
    for data_stream in user_model.get_streams():
        data_stream.shutdown_event.set()
    
    # wait for each thread to exit before shutdown
    for data_stream in user_model.get_streams():
        if data_stream.ident is not None or data_stream.is_alive():
            data_stream.join()
    
    root.destroy()

if __name__ == "__main__":
    
    # initialize user model
    user_model = UserModel()
    data_stream = SoftwareStream("software_stream_test", StreamType.SOFTWARE)
    data_stream.start()
    user_model.add_stream(data_stream)

    # create root and frame for the main window
    root = tk.Tk()
    root.wm_title('main window')
    frames = create_grid(root,2,2, frame_names)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # create device connector
    device_frame_viewmodel = EEGDeviceViewModel(user_model)
    device_connector = EEGDeviceFrame(frames[0][0], device_frame_viewmodel)

    # create plotter
    plotter = Plotter(frames[0][1], user_model)

    # create game
    #float_the_orb = FloatTheOrb(frames[1][0], user_context, user_context_lock)    
    #float_the_orb.start_pygame()

    # clicking (x) on main window prevents program from quiting while commands are being queued.
    # we'll need a quit event to propagate through the program to kill any future queued commands.
    root.mainloop()

