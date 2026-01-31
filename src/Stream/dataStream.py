from threading import Thread, Event
from common import QUEUE_LENGTH
from collections import deque
from enum import Enum
import numpy as np

class StreamType(Enum):
    DEVICE = 1
    FILTER = 2
    CONTROL = 3
    SOFTWARE = 4

class DataStream():
    def __init__(self, stream_name: str, 
                 stream_type: StreamType, 
                 queue_length: int = QUEUE_LENGTH):
        
        self.stream_name: str = stream_name
        self.stream_type: StreamType = stream_type
        self._queue_length: int = queue_length
        self.data: deque = deque(maxlen=queue_length)
        self._shutdown: bool = False 
        self.shutdown_event: Event = Event()
        self._stream_thread: Thread = None
    
    # return all data in the queue for the stream
    def get_stream_data(self) -> deque:
        return np.array(self.data).T
    
    # This function is meant to be implemented by the inheriting class.
    def _stream(self) -> None:
        try: 
            pass
        except:
            pass
    
    # start the streaming thread 
    def start(self) -> None:
        if self._stream_thread == None and not self.shutdown_event.is_set():
            self._stream_thread = Thread(target=self._stream)
            self._stream_thread.start()

    # stop the streaming thread and reset it to none
    def stop(self) -> None:
        if self._stream_thread is not None:
            self.shutdown_event.set()
            self.join()
            self.shutdown_event.clear()
            self._stream_thread = None

    # wait for streaming thread to finish
    def join(self) -> None:
        self._stream_thread.join()
    
    # check if thread is alive
    def is_alive(self) -> bool:
        if self._stream_thread == None:
            return False
        elif not (self._stream_thread.is_alive() or self._stream_thread.ident is not None):
            return False
        else:
            return True
        
    def to_dict(self) -> dict:
        return {
            'stream_name': self.stream_name,
            'stream_type': self.stream_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DataStream':
        stream_type = StreamType(data['stream_type'])
        return cls(data['stream_name'], stream_type, QUEUE_LENGTH)