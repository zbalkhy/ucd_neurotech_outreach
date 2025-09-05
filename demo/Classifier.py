from os import times
from time import time
import pandas as pd
import numpy as np
import math
from sklearn.linear_model import LogisticRegression
from scipy import signal
class Classifier:

    def __init__(self):
        self.model = None

    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        return signal.butter(order, [lowcut, highcut], fs=fs, btype='bandpass')

    def butter_bandstop(self, lowcut, highcut, fs, order=5):
        return signal.butter(order, [lowcut, highcut], fs=fs, btype='bandstop')

    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = signal.filtfilt(b, a, data)
        return y

    def butter_bandstop_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandstop(lowcut, highcut, fs, order=order)
        y = signal.filtfilt(b, a, data)
        return y

    def filterChannel(self, df):
        bandpassed = self.butter_bandpass_filter(df, 2, 40, 250, 1)
        bandstopped = self.butter_bandstop_filter(bandpassed, 59, 61, 250, 1)
        return bandstopped

    def getFreqsAveragesForChannel(self, channelDf, sampleRate):
        # note trials are 5 seconds long sampled at 250Hz. Only taking the last 3 sec
        twoSecondIndex = 0#int(sampleRate*2)
        freqAmplitudes = np.abs(np.fft.fft(channelDf[twoSecondIndex:]))
        freqs = np.fft.fftfreq(n=channelDf[twoSecondIndex:].size, d=1/sampleRate)
        
        #cut out imaginary part of the fft
        freqs = freqs[:math.floor(len(freqs)/2)]
        freqAmplitudes = freqAmplitudes[:math.floor(len(freqAmplitudes)/2)]

        #subset freqs and amplitudes to the frequenencies we care about
        startIndex = np.where(freqs>=6)[0][0]
        endIndex = np.where(freqs>=15)[0][0]
        
        freqs = freqs[startIndex:endIndex]
        freqAmplitudes = freqAmplitudes[startIndex:endIndex]

        #normalize frequencyAmplitudes
        freqAmplitudes = self.normalize(freqAmplitudes)

        #average frequency powers outside of alpha range and frequencies inside alpha range
        alphaAverage = 0
        aroundAlphaAverage = 0
        numFreqsAroundAlpha = 0
        numFreqsInAlpha = 0
        for i in range(len(freqAmplitudes)):
            if (freqs[i] >= 6 and freqs[i] < 8 or (freqs[i] > 12 and freqs[i] <= 14)):
                aroundAlphaAverage += freqAmplitudes[i]
                numFreqsAroundAlpha += 1
            if freqs[i] >= 8 and freqs[i] <= 12:
                alphaAverage += freqAmplitudes[i]
                numFreqsInAlpha += 1
        
        alphaAverage = alphaAverage / numFreqsInAlpha
        aroundAlphaAverage = aroundAlphaAverage / numFreqsAroundAlpha
        return alphaAverage, aroundAlphaAverage

    def normalize(self, data):
        minimum = np.amin(data)
        maximum = np.amax(data)
        minMaxDiff = maximum - minimum
        for i in range(len(data)):
            data[i] = (data[i] - minimum) / minMaxDiff
        return data

    def getAlphaAndNonalphaFreqAvgsPerChannel(self, df, sampleRate):
        channels = list(df.columns.values)
        alphaAvgPerChannel = []
        aroundAlphaAvgPerChannel = []
        for channel in list(channels):
            if "channel" not in channel:
                channels.remove(channel)
            else:
                #filter signal and then get freqs
                filtd = self.filterChannel(df[:][channel])
                alphaAverage, aroundAlphaAverage = self.getFreqsAveragesForChannel(filtd, sampleRate)
                alphaAvgPerChannel.append(alphaAverage)
                aroundAlphaAvgPerChannel.append(aroundAlphaAverage)
        return np.array(alphaAvgPerChannel), np.array(aroundAlphaAvgPerChannel)

    def predictSample(self, df, sampleRate):
        if (not self.model):
            return 0
        alphaAvgPerChannel, avgNonAlphaPerChannel = self.getAlphaAndNonalphaFreqAvgsPerChannel(df, sampleRate)
        prediction = self.model.predict(np.append(alphaAvgPerChannel, avgNonAlphaPerChannel).reshape(1, -1))
        return prediction

    def trainModel(self, samples, labels):
        print(samples)
        print(labels)
        # samples is a list of np arrays containing fft data, labels is a list of binary values 
        # we fit a logistic regression model to the averaged alpha band power per channel
        clf = LogisticRegression(random_state=0).fit(samples, labels)
        self.model = clf
        return clf

    def processDataAndTrainModel(self, experimentData, sampleRate):
        trainingData = []
        y_values = []
        for i in range(len(experimentData)):
            alphaAvgPerChannel, avgNonAlphaPerChannel = self.getAlphaAndNonalphaFreqAvgsPerChannel(experimentData[i]["data"], sampleRate)
            trainingData.append(np.append(alphaAvgPerChannel, avgNonAlphaPerChannel))
            y_values.append(experimentData[i]["trialType"])
        self.trainModel(trainingData, y_values)