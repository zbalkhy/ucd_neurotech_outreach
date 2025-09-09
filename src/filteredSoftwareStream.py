from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH, SAMPLING_FREQ
import numpy as np
from scipy import signal
from time import sleep
from userModel import UserModel

# attempting to create a filtered stream
class FilteredStream(DataStream):
    def __init__(self, 
                 reference_stream_name: str,
                 stream_name: str, 
                 stream_type: StreamType, 
                 user_model: UserModel,
                 filters: dict,
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)
        self.user_model = user_model
        self.reference_stream_name = reference_stream_name
        self.filter_info = filters

    def _stream(self):

        data = []
        try:
            while not self.shutdown_event.is_set():
                for stream in self.user_model.get_streams():
                    #checks for the reference stream in the user model
                    if stream.stream_name == self.reference_stream_name:

                        #takes data from the reference stream
                        held_data = np.array(list(stream.get_stream()))

                        #for each filter, take the necessary information out
                        for i in range(len(self.filter_info['filter'])):
                            filter_type = self.filter_info['filter'][i]
                            cutoff_freq = np.array(self.filter_info['frequency'][i])
                            filter_order = self.filter_info['order'][i]

                            #normalize the cutoff frequency to the sampling rate
                            normalized_cutoff = cutoff_freq / (.5 * SAMPLING_FREQ)

                            #filter the signal
                            b, a = signal.butter(filter_order, normalized_cutoff, btype=filter_type, analog=False)
                            held_data = signal.lfilter(b, a, held_data)
                            
                        #update the data
                        self.data = list(held_data)
                        sleep(1/SAMPLING_FREQ)
                        break
        except:
            pass