import tkinter as tk
import numpy as np
from Classes.featureClass import *
from View.featureView import FeatureView
from src.ViewModel.featureViewModel import FeatureViewModel
from Models.userModel import UserModel
from common import split_dataset

if __name__ == "__main__":
    # initialize tk, setup root and frame
    root = tk.Tk()
    root.wm_title('feature module test')
    frame = tk.Frame(root, borderwidth=2, relief="solid")

    # construct user model
    user_model = UserModel()
    
    # add default features to the user model
    for type in FeatureType:
        if type != FeatureType.CUSTOM:
            user_model.add_feature(FeatureClass(type))
    
    # load test dataset
    import os
    # load test dataset
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/eeg-eye-state.csv')
    df = pd.read_csv(csv_path)

    # extract fs hardcode for this dataset right now
    fs = df.shape[0]/117
    
    # split trials
    data0 = df.loc[df['class'] == 0]
    data1 = df.loc[df['class'] == 1]
    nsamples = 50
    ntrials = 50

    data0 = split_dataset(data0, nsamples, ntrials)
    data1 = split_dataset(data1, nsamples, ntrials)

    #user_model.add_dataset("data0", data0)
    #user_model.add_dataset("data1", data1)

    # create view and view model
    feature_view_model = FeatureViewModel(user_model)
    feature_view = FeatureView(frame, feature_view_model)
    frame.pack()
    
    root.mainloop()