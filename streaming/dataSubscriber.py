"""Example program to show how to read a multi-channel time series from LSL."""

from pylsl import StreamInlet, resolve_streams
from time import sleep
import numpy as np

class DataSubscriber():
    def __init__(self):
        self.currentChunk = None

        streams = resolve_streams()
        self.inlet = StreamInlet(streams[0])


    def pull_chunk(self) -> np.ndarray:
        chunk, timestamp = self.inlet.pull_chunk()
        return np.array(chunk) 
    
    def main(self):
        while True:
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            chunk, timestamp = self.inlet.pull_chunk()
            print(chunk)
            sleep(1)
            
if __name__ == "__main__":
    sub = DataSubscriber()
    sub.main()

