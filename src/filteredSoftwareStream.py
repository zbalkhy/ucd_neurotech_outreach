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
                processed_data = self.filter_obj.filter_data(held_data)
                self.data = list(processed_data)
                sleep(1/SAMPLING_FREQ)
        except:
            pass