from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH
import numpy as np
from time import sleep

# this is a quick class which right now is just a sinusoid stream. 
# if we eventually decide to add a signal generator module, this will come in handy
class SoftwareStream(DataStream):
    def __init__(self, stream_name: str, 
                 stream_type: StreamType, 
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)

    def _stream(self):
        t=0
        try:
            while not self.shutdown_event.is_set():
                self.data.append(15*np.sin(0.01*np.pi*t) + 12*np.sin(0.03*np.pi*t) + 1*np.sin(0.15*np.pi*t) + 11*np.sin(0.07*np.pi*t))
                t += 1
                sleep(0.004)
        except:
            pass