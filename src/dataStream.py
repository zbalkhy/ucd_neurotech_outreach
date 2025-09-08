from threading import Thread, Event
from common import QUEUE_LENGTH
from collections import deque
from enum import Enum

class StreamType(Enum):
    DEVICE = 1
    FILTER = 2
    CONTROL = 3
    SOFTWARE = 4

class DataStream(Thread):
    def __init__(self, stream_name: str, 
                 stream_type: StreamType, 
                 queue_length: int = QUEUE_LENGTH):
        
        self.stream_name: str = stream_name
        self.stream_type: StreamType = stream_type
        self._queue_length: int = queue_length
        self.data: deque = deque(maxlen=queue_length)
        self._shutdown: bool = False 
        self.shutdown_event: Event = Event()

        super().__init__()
    
    # return all data in the queue for the stream
    def get_stream(self) -> deque:
        return self.data
    
    # This function is meant to be implemented by the inheriting class.
    def _stream(self) -> None:
        try: 
            pass
        except:
            pass
    
    # define what to do when the thread is started
    def run(self):
        while not self.shutdown_event.is_set():
            self._stream()
