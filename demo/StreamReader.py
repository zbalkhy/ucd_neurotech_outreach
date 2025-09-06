from os import times
from time import time
from pylsl import StreamInlet
import datetime
from multiprocessing import Process
from multiprocessing import Queue
from threading import Thread

class StreamReader:
    def __init__(self, bufferSize, stream):
        self.dataBuffer = Queue()
        self.bufferLength = bufferSize
        self.sampleRate = 250 #self.stream.nominal_srate
        self.channel_count = 8 # self.stream.channel_count
        self.stream = stream
        self.streamProcess = Thread(target=self.__readStream__)
        self.streamProcess.start()
        self.continueStreaming = True
    
    def __readStream__(self):
        try:
            # create a new inlet to read from the stream
            inlet = StreamInlet(self.stream)
            curSecond = []
            while self.continueStreaming:
                # get a new sample (you can also omit the timestamp part if you're not
                # interested in it)
                sample, timestamp = inlet.pull_sample()

                # add time correction to get system local time, and append timestamp to data
                
                timestamp =  timestamp + inlet.time_correction()
                if sample:
                    sample.append(timestamp)
                curSecond.append(sample)
                if len(curSecond) == self.sampleRate:
                    i = 0
                    try:
                        self.dataBuffer.put(curSecond, timeout=False)
                    except:
                        print("queue full")
                    curSecond = []
                    
        except KeyboardInterrupt as e:
            print("Stream reader stopped")
            raise e

    def getSecondWorthOfData(self):
        if self.dataBuffer.empty():
            return []
        else:
            try:
                return self.dataBuffer.get(timeout=False)
            except Queue.Empty:
                return []
    def shutDownStreamer(self):
        self.continueStreaming = False
    

    
    
