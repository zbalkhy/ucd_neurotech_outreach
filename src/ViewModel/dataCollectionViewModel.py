from Models.userModel import UserModel
from numpy import ndarray
import numpy as np


class dataCollectionViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model
        self.dataset = np.array([])
        self.first_trial = False
        self.labelset = np.array([])
        self.collecting = False

    # creating new dataset
    def clear_dataset(self) -> None:
        self.labelset = np.array([])
        self.dataset = np.array([])

    def start_collecting(self) -> None:
        self.collecting = True

    def get_unique_labels(self) -> list:
        # sends out ordered list
        _, idx = np.unique(self.labelset, return_index=True)
        return self.labelset[np.sort(idx)].tolist()

    def add_dataset(self, collection_stream: str, label: str) -> None:
        if self.collecting:
            stream = self.user_model.get_stream(collection_stream)
            data = np.array(list(stream.get_stream_data()))
            axis = self.dataset.ndim
            self.labelset = np.append(self.labelset, label)  # add label to labelset
            if self.dataset.size == 0:
                # if dataset is empty, populate
                self.dataset = data
                self.first_trial = True
            elif axis != data.ndim:
                # add to largest axis
                self.dataset = np.append(self.dataset, np.array([data]), axis= 0)
            else:
                # if data set only has one entry, make new axis
                self.dataset = np.stack([self.dataset, data], axis= 0)
                self.first_trial = False

    def get_trial_number(self) -> int:
        if self.first_trial:
            return 1
        else:
            size = self.dataset.shape
            return size[0]
        
    def save_dataset(self, name: str) -> None:
        self.collecting = False
        unique_labels = self.get_unique_labels()
        for idx, value in enumerate(unique_labels):
            # replace str with corresponding number
            self.labelset[value == self.labelset] = idx
        # change to integer numpy array
        self.labelset = self.labelset.astype(int)
        self.user_model.add_dataset(name, self.dataset)
        self.user_model.add_labelset(name, self.labelset)  # treats labelset like a dataset

    def get_streams(self):
        return self.user_model.get_streams()
