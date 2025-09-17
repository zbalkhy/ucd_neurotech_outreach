import numpy as np
from numpy import ndarray
from common import SAMPLING_FREQ
from scipy import signal
class filterClass():
    def __init__(self, filter_name: str):
        self.filter_name: str = filter_name
        self.filters: dict = {'filter': [], 'order': [], 'frequency': []}
    def get_filters(self):
        return self.filters
    def add_filters(self, name: str, value: str or float):
        self.filters[name].append(value)
    
    def filter_data(self, data: ndarray):
        held_data = data
        for i, x in enumerate(self.filters['filter']):
            filter_type = self.filters['filter'][i]
            cutoff_freq = np.array(self.filters['frequency'][i])
            filter_order = self.filters['order'][i]
            normalized_cutoff = cutoff_freq / (.5 * SAMPLING_FREQ)
            b, a = signal.butter(filter_order, normalized_cutoff, btype=filter_type, analog=False)
            held_data = signal.lfilter(b, a, held_data)
        return held_data