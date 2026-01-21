import numpy as np
from numpy import ndarray
from scipy import signal
from typing import Union

class FilterClass():
    def __init__(self, filter_name: str):
        self.filter_name: str = filter_name
        self.filters: dict = {'filter': [], 'order': [], 'frequency': []}
    
    def get_filters(self) -> None:
        return self.filters
    
    def add_filters(self, name: str, value: Union[str, float]) -> None:
        self.filters[name].append(value)
    
    def filter_data(self, data: ndarray, fs: int) -> ndarray:
        for i, x in enumerate(self.filters['filter']):
            filter_type = self.filters['filter'][i]
            cutoff_freq = np.array(self.filters['frequency'][i])
            filter_order = self.filters['order'][i]
            normalized_cutoff = cutoff_freq / (.5 * fs)
            b, a = signal.butter(filter_order, normalized_cutoff, btype=filter_type, analog=False)
            data = signal.filtfilt(b, a, data, axis = -1)
        return data
    
    def apply(self, data: ndarray, fs: int) -> ndarray:
        return self.filter_data(data, fs)