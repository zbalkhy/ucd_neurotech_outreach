from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH
import numpy as np
from time import sleep

class SoftwareStream(DataStream):
    def __init__(self, stream_name: str, 
                 stream_type: StreamType, 
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)

    def _stream(self):
        t=0
        try:
            while not self.shutdown_event.is_set():
                self.data.append(15*np.sin(0.01*np.pi*t))
                t+=1
                sleep(0.004)
        except:
            pass