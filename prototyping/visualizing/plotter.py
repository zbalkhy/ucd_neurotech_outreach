from matplotlib import pyplot as plt
import numpy as np
from streaming.dataSubscriber import DataSubscriber
from scipy import signal

class Plotter():
    def __init__(self, window_size, fs):
        self.sampleRate = fs
        self.dataSubscriber = DataSubscriber()
        self.window_size = window_size
        self.current_chunk = np.zeros(self.window_size) + 0.0000001
        return
    
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

    def filter_chunk(self):
        # we're just doing a butter band pass over the alpha ranges.
        b, a = signal.butter(6, [8 / self.sampleRate * 2, 13 / self.sampleRate * 2], btype='bandpass')
        self.current_chunk = signal.filtfilt(b, a, self.current_chunk) / max(abs(signal.filtfilt(b, a, self.current_chunk))) * max(abs(self.current_chunk))

    def get_fft(self, chunk):
        freqs = np.fft.fftfreq(chunk.shape[0], d=1/128)
        fft = np.fft.fft(chunk)
        return np.abs(fft), freqs
    
    def plot(self):
        self.read_chunk()
        self.filter_chunk()
        fft, freqs = self.get_fft(self.current_chunk)
        fft_xlims = (5,30)
        x = np.arange(0, self.window_size)

        fft_min = np.min(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))])
        fft_max = np.max(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))])

        O2_max = np.max(self.current_chunk)
        O2_min = np.min(self.current_chunk)

        plt.ion()

        fig = plt.figure(figsize = (10,4))
        ax1 = fig.add_subplot(121)
        ax1.set_title("Filtered O2 EEG signal")
        ax1.set_ylabel("amplitude")
        ax1.set_xlabel("time")
        line1, = ax1.plot(x, self.current_chunk, 'r-') # Returns a tuple of line objects, thus the comma

        ax2 = plt.subplot(122)
        ax2.set_title("frequency spectrum")
        ax2.set_xlabel("freq (Hz)")
        ax2.set_ylabel('power')
        ax2.set_ylim(fft_min, fft_max)
        ax2.set_xlim(fft_xlims)
        line2, = ax2.plot(np.fft.fftshift(freqs), np.fft.fftshift(fft))
        
        while True:
            self.read_chunk()
            self.filter_chunk()
            fft, freqs = self.get_fft(self.current_chunk)
            
            line1.set_ydata(self.current_chunk)
            ax1.set_ylim((O2_min, O2_max))
            
            if O2_max < np.max(self.current_chunk):
                O2_max = np.max(self.current_chunk)
            if O2_min > np.min(self.current_chunk):
                O2_min = np.min(self.current_chunk)
            
            line2.set_ydata(np.fft.fftshift(fft))
            
            if fft_min > np.min(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))]):
                fft_min = np.min(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))])
            if fft_max < np.max(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))]):
                fft_max = np.max(fft[np.where((freqs >= fft_xlims[0]) & (freqs <= fft_xlims[1]))])
            ax2.set_ylim(fft_min, fft_max)

            fig.canvas.draw()
            fig.canvas.flush_events()