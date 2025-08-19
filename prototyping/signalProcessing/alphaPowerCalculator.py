from streaming.dataSubscriber import DataSubscriber
import numpy as np
import scipy.stats as stats
from scipy import signal

class AlphaPowerCalculator():
    def __init__(self, window_size, fs):
        # include a step for moving average filter
        self.dataSubscriber = DataSubscriber()
        self.window_size = window_size
        self.sampleRate = fs
        self.current_chunk = np.zeros(self.window_size) + 0.00001

    def get_power(self):
        self.read_chunk()
        self.filter_chunk()

        freqs = np.fft.fftfreq(self.current_chunk.shape[0], d=1/self.sampleRate)
        chunk_fft = np.fft.fft(self.current_chunk)
        chunk_power = np.abs(chunk_fft)
        alpha_power = np.sum(chunk_power[np.where((freqs>= 8) & (freqs <=13))]**2)

        return alpha_power
    
    def read_chunk(self):
        new_chunk = self.dataSubscriber.pull_chunk()
        # possible to not have any new data
        if new_chunk.size == 0:
            return
        
        # we are sending all data along the stream, but in a real scenario we'll only have 1 channel
        # so just take the O2 channel i'm hard coding the O2 index for now.
        new_chunk = new_chunk[:,7]
        
        if new_chunk.size >= self.window_size:
            # if there is more data in the chunk than the window allows, just take the most recent data
            self.current_chunk = new_chunk[new_chunk.size - self.window_size:]
        elif new_chunk.size < self.window_size:
            # if there isn't enough data to fill a new chunk, then assume we have continuous data and tack it on to the end
            new_chunk = np.hstack((self.current_chunk, new_chunk))
            self.current_chunk = new_chunk[new_chunk.size - self.window_size:]
        print(self.current_chunk.size)
    
    def filter_chunk(self):
        # we're just doing a butter band pass over the alpha ranges.
        b, a = signal.butter(6, [8 / self.sampleRate * 2, 13 / self.sampleRate * 2], btype='bandpass')
        self.current_chunk = signal.filtfilt(b, a, self.current_chunk) / max(abs(signal.filtfilt(b, a, self.current_chunk))) * max(abs(self.current_chunk))
