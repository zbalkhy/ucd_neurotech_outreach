from dataStream import *
from threading import Lock
from eventClass import EventClass, EventType

class UserModel(EventClass):
    def __init__(self):
        self.data_streams: dict = {}
        self.lock: Lock = Lock()
        super().__init__()

    def on_notify(self, eventData: any, event: EventType ) -> None:
        # no need to implement this function here yet.
        pass

    def get_stream(self, name: str) -> DataStream:
        if name in self.data_streams.keys():
            return self.data_streams[name]
        else:
            return None
    
    def get_streams(self) -> list[DataStream]:
        return list(self.data_streams.values())
    
    def add_stream(self, stream: DataStream) -> None:
        ##UTILIZE THIS TO ADD STREAM LATER
        
        ##TODO: right now there is a bug where
        ## if a user overrides a stream with the same name, the program loses track of the old stream thread and cannot quit

        self.data_streams[stream.stream_name] = stream

        if stream.stream_type in [StreamType.SOFTWARE, StreamType.DEVICE]:
            self.notify(None, EventType.DEVICELISTUPDATE)

    

    