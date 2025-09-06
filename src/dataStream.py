from threading import Thread
from eventClass import EventClass
from eventType import EventType
from common import QUEUE_LENGTH
from collections import deque

class DataStream(EventClass):
    def __init__(self, stream_name: str, events: EventClass, queue_length: int = QUEUE_LENGTH):
        self.stream_name: str = stream_name
        self._queue_length: int = queue_length
        self.data: deque = deque(maxlen=queue_length)
        self._shutdown: bool = False 
        self.stream_thread: Thread = None
        self.events: EventClass = events

        self.events.add_observer(self)
        super().__init__()

    def on_notify(self, eventData: any, event: EventType) -> None:
        if event == EventType.PROGRAMEXIT:
            self.shutdown = True
    
    def get_stream(self) -> deque:
        return self.data
    
    def _stream(self) -> None:
        try:
            pass
        except:
            pass
    
    def start_stream(self) -> None:
        if self._stream_thread == None:
            self._stream_thread = Thread(target=self._stream)
            self._stream_thread.start()
