from threading import Thread, Event
from common import QUEUE_LENGTH
from collections import deque

class DataStream(Thread):
    def __init__(self, stream_name: str, queue_length: int = QUEUE_LENGTH):
        self.stream_name: str = stream_name
        self._queue_length: int = queue_length
        self.data: deque = deque(maxlen=queue_length)
        self._shutdown: bool = False 
        self.stream_thread: Thread = None
        self.shutdown_event: Event = Event()

        super().__init__()
    
    def get_stream(self) -> deque:
        return self.data
    
    def _stream(self) -> None:
        # This function is meant to be implemented by the inheriting class.
        try:
             
            pass
        except:
            pass
    
    def run(self):
        while not self.shutdown_event.is_set():
            self._stream()
