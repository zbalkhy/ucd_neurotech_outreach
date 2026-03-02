import numpy as np
from time import sleep
from typing import Union
from Classes.filterClass import FilterClass
from Classes.featureClass import FeatureClass
from Classes.classifierClass import Classifier
from Stream.dataStream import *
from common import SAMPLING_FREQ

class ComposedStream(DataStream):
    def __init__(self, 
                 reference_stream: DataStream,
                 transformations: list[Union[FeatureClass, FilterClass, Classifier]],
                 stream_name: str,
                 stream_type: StreamType,
                 queue_length: int = QUEUE_LENGTH,
                 window_size: int = None):
        super().__init__(stream_name, stream_type, queue_length)
        self.reference_stream = reference_stream
        self.stream_name = stream_name
        self.transformations = transformations
        self.window_size = window_size

    def _stream(self):
        try:
            while not self.shutdown_event.is_set():
                new_data = np.array(list(self.reference_stream.data))
                
                # If window_size is set, only use the last window_size samples
                if self.window_size and len(new_data) >= self.window_size:
                    new_data = new_data[-self.window_size:]
                    
                    # Process the window
                    for transformation in self.transformations:
                        new_data = transformation.apply(new_data, SAMPLING_FREQ)
                    self.data.extend(list(new_data))
                    
                    # Wait before next classification
                    sleep(0.5)  # Classify twice per second
                else:
                    # Original behavior for non-windowed mode
                    for transformation in self.transformations:
                        new_data = transformation.apply(new_data, SAMPLING_FREQ)
                    self.data.extend(list(new_data))
                    sleep(1/SAMPLING_FREQ)
        except Exception as e:
            print(e)