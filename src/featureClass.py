from enum import Enum
from numpy import abs, logical_and, ndarray, dtype
from numpy.fft import rfft, rfftfreq
from common import *
from typing import Tuple

class FeatureType(Enum):
    DELTA = 1
    THETA = 2
    ALPHA = 3
    BETA = 4
    GAMMA = 5
    CUSTOM = 6

class FeatureClass():
    def __init__(self, feature_type:FeatureType):
        self.type = feature_type
        return

    def get_fft(self, data: any, fs: int) -> Tuple[ndarray, ndarray]:
        freqs = rfftfreq(len(data), 1 / fs)
        psd = abs(rfft(data)) ** 2
        return psd, freqs
    
    def apply(self, data: any, fs: int) -> ndarray:
        if self.type != FeatureType.CUSTOM:
            psd, freqs = self.get_fft(data, fs)
            match self.type:
                case FeatureType.DELTA:
                    idx = logical_and(freqs >= DELTA[0], freqs <= DELTA[1])
                case FeatureType.THETA:
                    idx = logical_and(freqs >= THETA[0], freqs <= THETA[1])
                case FeatureType.ALPHA:
                    idx = logical_and(freqs >= ALPHA[0], freqs <= ALPHA[1])
                case FeatureType.BETA:
                    idx = logical_and(freqs >= BETA[0], freqs <= BETA[1])
                case FeatureType.GAMMA:
                    idx = logical_and(freqs >= GAMMA[0], freqs <= GAMMA[1])
                case _:
                    idx = list(range(freqs.size))
            return psd[idx].mean(axis=0)
        

            


    
