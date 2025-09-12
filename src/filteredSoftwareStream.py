from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH, SAMPLING_FREQ
import numpy as np
from scipy import signal
from time import sleep
from userModel import UserModel
from filterClass import filterClass

# attempting to create a filtered stream
class FilteredStream(DataStream):
    def __init__(self, 
                 reference_stream: DataStream,
                 filter_obj: filterClass,
                 stream_name: str, 
                 stream_type: StreamType, 
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)
        self.reference_stream = reference_stream
        self.stream_name = stream_name
        self.filter_obj = filter_obj

    def _stream(self):
        #access the filter information with the corresponding filter
        filter_dict = self.filter_obj.get_filters()
        data = []
        print(self.reference_stream)
        try:
            while not self.shutdown_event.is_set():
                held_data = np.array(list(self.reference_stream.get_stream()))
                for i, x in enumerate(filter_dict['filter']):
                    #loop through each filter
                    filter_type = filter_dict['filter'][i]
                    cutoff_freq = np.array(filter_dict['frequency'][i])
                    filter_order = filter_dict['order'][i]
                    #normalize the cutoff frequency to the sampling rate
                    normalized_cutoff = cutoff_freq / (.5 * SAMPLING_FREQ)
                    #filter the signal
                    b, a = signal.butter(filter_order, normalized_cutoff, btype=filter_type, analog=False)
                    held_data = signal.lfilter(b, a, held_data)
                #update the data
                self.data = list(held_data)
                sleep(1/SAMPLING_FREQ)
        except:
            pass