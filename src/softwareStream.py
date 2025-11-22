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
                waveform_ch1 = (15*np.sin(0.01*np.pi*t) + 
                                 12*np.sin(0.03*np.pi*t) + 
                                 1*np.sin(0.15*np.pi*t) + 
                                 11*np.sin(0.07*np.pi*t))
                waveform_ch2 = (3*np.sin(0.02*np.pi*t) + 
                                 7*np.sin(0.1*np.pi*t) + 
                                 8*np.sin(0.04*np.pi*t) + 
                                 4*np.sin(0.08*np.pi*t))
                self.data.append([waveform_ch1, waveform_ch2])
                t += 1
                sleep(0.004)
        except:
            pass