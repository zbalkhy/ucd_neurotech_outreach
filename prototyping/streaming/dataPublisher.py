import time
import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy import interpolate
from random import random as rand
from pylsl import StreamInfo, StreamOutlet, local_clock


class DataPublisher:
    def __init__(self):
        self.sampleRate = 250
        self.dataFile = "/Users/zacariabalkhy/neurotech_outreach/data/eeg-eye-state.csv"
        self.dataIndex = 0
        self.dataSize = 0
        self.data = None
        self.t = None

    def interp(self, x):
        t_temp = self.t[x.index[~x.isnull()]]
        x = x[x.index[~x.isnull()]]
        clf = interpolate.interp1d(t_temp, x, kind='cubic')
        return clf(self.t)

    def loadData(self, fileName):
        # this is all very hand wavy for now.
        # because of that we are heavily preprocessing the data
        df = pd.read_csv(fileName)
        fs = df.shape[0] / 117
        self.sampleRate = fs
        self.t = np.arange(0, len(df) * 1 / fs, 1 / fs)

        # Data comes in channel and eye state, separate the state out
        Y = df['class']
        X = df.drop(columns="class")

        # Find outliers and put Nan instead
        X = X.apply(stats.zscore, axis=0)
        X = X.applymap(lambda x: np.nan if (abs(x) > 4) else x)

        # recalculate outliers ignoring nans since the first calculation was
        # biased with the huge outliers!
        X = X.apply(stats.zscore, nan_policy='omit', axis=0)
        X = X.applymap(lambda x: np.nan if (abs(x) > 4) else x)

        # interpolate the nans using cubic spline method
        X_interp = X.apply(self.interp, axis=0)
        return np.array(X_interp)

    def main(self):
        srate = self.sampleRate
        name = 'MockDataSender'
        type = 'EEG'
        n_channels = 14

        self.data = self.loadData(self.dataFile)
        self.dataSize = self.data.shape[0]
        print(self.data.shape)
        # first create a new stream info (here we set the name to BioSemi,
        # the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
        # last value would be the serial number of the device or some other more or
        # less locally unique identifier for the stream as far as available (you
        # could also omit it but interrupted connections wouldn't auto-recover)
        info = StreamInfo(name, type, n_channels, srate,
                          'float32', 'myuid34234')

        # next make an outlet
        outlet = StreamOutlet(info)

        print("now sending data...")
        start_time = local_clock()
        sent_samples = 0
        while True:
            elapsed_time = local_clock() - start_time
            required_samples = int(srate * elapsed_time) - sent_samples
            for sample_ix in range(required_samples):
                # make a new random n_channels sample; this is converted into a
                # pylsl.vectorf (the data type that is expected by push_sample)
                mysample = self.data[self.dataIndex, :]
                # now send it
                outlet.push_sample(mysample)
                self.dataIndex += 1
                if self.dataIndex == self.dataSize:
                    self.dataIndex = 0
            sent_samples += required_samples
            # now send it and wait for a bit before trying again.
            time.sleep(1 / self.sampleRate)


if __name__ == '__main__':
    dataMock = DataPublisher()
    dataMock.main()
