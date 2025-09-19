import numpy as np
from time import sleep
from typing import Union
from filterClass import FilterClass
from featureClass import FeatureClass
from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH, SAMPLING_FREQ

class ComposedStream(DataStream):
    def __init__(self, 
                 reference_stream: DataStream,
                 transformations: list[Union[FeatureClass, FilterClass]],
                 stream_name: str,
                 stream_type: StreamType,
                 queue_length: int = QUEUE_LENGTH):
        super().__init__(stream_name, stream_type, queue_length)
        self.reference_stream = reference_stream
        self.stream_name = stream_name
        self.transformations = transformations

    def _stream(self):
        #access the filter information with the corresponding filter
        try:
            while not self.shutdown_event.is_set():
                new_data = np.array(list(self.reference_stream.get_stream_data()))
                for transformation in self.transformations:
                    new_data = transformation.apply(new_data, SAMPLING_FREQ)
                self.data.extend(list(new_data))
                sleep(1/SAMPLING_FREQ)
        except Exception as e:
            print(e)
            pass