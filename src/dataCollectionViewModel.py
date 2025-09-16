from userModel import UserModel
from numpy import ndarray
import numpy as np

class dataCollectionViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model
        self.dataset = np.array([])
        self.first_trial = False

    #creating new dataset
    def clear_dataset(self) -> None:
        self.dataset = np.array([])

    def add_dataset(self, collection_stream: str) -> None:
        stream = self.user_model.get_stream(collection_stream)
        data = np.array(list(stream.get_stream()))
        axis = self.dataset.ndim
        if self.dataset.size == 0:
            #if dataset is empty, populate
            self.dataset = data
            self.first_trial = True
        elif axis != data.ndim:
            #add to largest axis
            self.dataset = np.append(self.dataset, np.array([data]), axis = 0)
        else:
            #if data set only has one entry, make new axis
            self.dataset = np.stack([self.dataset, data], axis = 0)
            self.first_trial = False
    def get_trial_number(self) -> int:
        if self.first_trial == True:
            return 1
        else:
            axis = self.dataset.ndim
            size = self.dataset.shape
            return size[0]

    def save_dataset(self, name: str) -> None:
        self.user_model.add_dataset(name, self.dataset)

    def get_streams(self):
        return self.user_model.get_streams()
        
        