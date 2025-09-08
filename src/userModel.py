from dataStream import DataStream

class UserModel(object):
    def __init__(self):
        self.dataStreams: dict = {}
    
    def get_stream(self, name: str) -> DataStream:
        if name in self.dataStreams.keys():
            return self.dataStreams[name]
        else:
            return None
        
    def add_stream(self, stream: DataStream) -> None:
        self.dataStreams[stream.stream_name] = stream

    