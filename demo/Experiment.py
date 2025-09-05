import cv2
import threading
import time
from playsound import playsound
from datetime import datetime
import numpy as np
import json
from pylsl import StreamInlet, resolve_streams
import multiprocessing as mp
from threading import Thread
from time import sleep
import pandas as pd

class Experiment:
    def __init__(self, numTrials, trialLength):
        self.numTrials = numTrials
        self.trialLength = trialLength
        self.dataStreamProcess = None
        self.experimentProcess = None
        self.EEGdata = []
        self.experimentMetaData = []  
        self.streamReady = False
        self.experimentComplete = False
        self.lastTimeStamp = 0
        self.trialSeparatedData = []
        self.sampleRate = 0

    def beginExperimentAndCollectMetaData(self):
        while(not self.streamReady):
            sleep(1)
        experimentStartTime = datetime.now()
        eyesClosed = cv2.imread(".\\Resources\\eyesClosed.jpg")
        eyesOpen = cv2.imread(".\\Resources\\eyesOpen.jpg")
        for i in range(self.numTrials):
            dp = {}
            dp["trialNumber"] = i
            if i % 2 == 0:
                dp["trialType"] = "eyesOpen"
                dp["trialStartTime"] = self.lastTimeStamp
                #t = threading.Thread(target=playsound, args=[r'.\\Resources\\doorbellTone.wav']).start()
                cv2.imshow("window", eyesOpen)
                cv2.waitKey(self.trialLength * 1000)
                cv2.destroyAllWindows()
            else:
                dp["trialType"] = "eyesClosed"
                dp["trialStartTime"] = self.lastTimeStamp
                cv2.imshow("window", eyesClosed)
                cv2.waitKey(self.trialLength * 1000)
                cv2.destroyAllWindows()
            dp["trialEndTime"] = self.lastTimeStamp #trialEndTime.strftime("%d-%b-%Y %H:%M:%S.%f")
            self.experimentMetaData.append(dp)
        self.experimentComplete = True

    def collectData(self):
        print("looking for an EEG stream...")
        streams = resolve_streams()
        if not streams or not streams[0]:
           print("no streams found")
           return
        self.sampleRate = streams[0].nominal_srate()
        inlet = StreamInlet(streams[0], processing_flags=0)
        inlet.time_correction()
        self.streamReady = True
        while not self.experimentComplete:
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            sample, timeStamp = inlet.pull_sample()
            self.lastTimeStamp = timeStamp + inlet.time_correction()
            # add time correction to get system local time, and append timestamp to data
            #timestamp += inlet.time_correction()
            if sample:
                sample.append(self.lastTimeStamp)
            self.EEGdata.append(sample)
    
    def runExperiment(self):
        self.dataStreamProcess = Thread(target=self.collectData)
        self.experimentProcess = Thread(target=self.beginExperimentAndCollectMetaData)
        print("1")
        self.dataStreamProcess.start()
        print("2")
        self.experimentProcess.start()
        print("3")
        self.experimentProcess.join()
        print("4")
        self.dataStreamProcess.join()
        print("5")
            
    def cleanData(self):
        columns = ["channel1", "channel2", "channel3", "channel4", "channel5", "channel6", "channel7", "channel8", "timestamp"]
        df = pd.DataFrame(self.EEGdata, columns=columns)
        df = df = df.apply(pd.to_numeric, errors='coerce')
        self.splitRawDataIntoTrials(df)
    
    def splitRawDataIntoTrials(self, df):
        trial = {}
        for i in range(len(self.experimentMetaData)):
            print(self.experimentMetaData[i])
            trial = self.experimentMetaData[i]
            trialStartTimeValMask = df["timestamp"] == float(trial["trialStartTime"])
            trialEndTimeValMask = df["timestamp"] == float(trial["trialEndTime"])
            trialStartIndex = df["timestamp"][trialStartTimeValMask].index.values[0]
            trialEndIndex = df["timestamp"][trialEndTimeValMask].index.values[0]
            trialDf = df.iloc[trialStartIndex:trialEndIndex,:]
            trialDf = trialDf.reset_index(drop=True)
            trial["data"] = trialDf
            self.trialSeparatedData.append(trial)
    



    
