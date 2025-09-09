from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH
import numpy as np
from scipy import signal
from time import sleep
from userModel import UserModel

# attempting to create a filtered stream
class FilteredStream(DataStream):
    def __init__(self, stream_name: str, 
                 stream_type: StreamType, 
                 user_model: UserModel,
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)
        self.user_model = user_model

    def _stream(self):

        data = []
        try:
            while not self.shutdown_event.is_set():
                for stream in self.user_model.get_streams():
                    if stream.stream_type == StreamType.SOFTWARE:
                        held_data = np.array(list(stream.get_stream()))

                        cutoff_freq = 30 #in hz
                        fs = 250 #in hz
                        nyquist = .5 * fs
                        normal_cutoff = cutoff_freq / nyquist
                        order = 4
                        
                        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
                        filtered_data = signal.lfilter(b, a, held_data)
                        
                        self.data = list(filtered_data)
                        sleep(.004)
                        break
        except:
            pass