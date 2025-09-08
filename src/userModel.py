from dataStream import DataStream
from threading import Lock

class UserModel(object):
    def __init__(self):
        self.data_streams: dict = {}
        self.lock: Lock = Lock()
    
    def get_stream(self, name: str) -> DataStream:
        if name in self.data_streams.keys():
            return self.data_streams[name]
        else:
            return None
    
    def get_streams(self) -> list[DataStream]:
        return list(self.data_streams.values())
    
    def add_stream(self, stream: DataStream) -> None:
        self.data_streams[stream.stream_name] = stream

    

    