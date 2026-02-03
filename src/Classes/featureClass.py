from enum import Enum
from numpy import abs, logical_and, ndarray
from numpy.fft import rfft, rfftfreq
from common import *
from typing import Tuple
from types import FunctionType


class FeatureType(Enum):
    DELTA = 1
    THETA = 2
    ALPHA = 3
    BETA = 4
    GAMMA = 5
    CUSTOM = 6


class FeatureClass():
    def __init__(self, feature_type: FeatureType,
                 custom_name: str = None,
                 custom_function: FunctionType = None):
        self.type = feature_type
        self.custom_name = custom_name
        self.custom_function = custom_function

    def __str__(self):
        match self.type:
            case FeatureType.DELTA:
                return "Delta Power"
            case FeatureType.THETA:
                return "Theta Power"
            case FeatureType.ALPHA:
                return "Alpha Power"
            case FeatureType.BETA:
                return "Beta Power"
            case FeatureType.GAMMA:
                return "Gamma Power"
            case _:
                return self.custom_name

    def get_fft(self, data: ndarray, fs: int) -> Tuple[ndarray, ndarray]:
        freqs = rfftfreq(data.shape[0], 1 / fs)
        psd = abs(rfft(data, axis=0)) ** 2
        return psd, freqs

    def apply(self, data: ndarray, fs: int) -> ndarray:
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
            return psd[np.where(idx)].mean(axis=0)
        else:
            try:
                return self.custom_function(data, fs)
            except BaseException:
                # need to have some way to bubble up that the function is not
                # valid
                pass

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'custom_name': self.custom_name,
            #save custom_function later, when it is implemented
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FeatureClass':
        feature_type = FeatureType(data['type'])
        return cls(feature_type, custom_name=data.get('custom_name'))
