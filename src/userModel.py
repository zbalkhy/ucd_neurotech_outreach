from dataStream import *
from threading import Lock
from eventClass import EventClass, EventType
from filterClass import filterClass
from numpy import ndarray

class UserModel(EventClass):
    def __init__(self):
        self.data_streams: dict = {}
        self.filters: dict = {}
        self.data_sets: dict[str, ndarray] = {}
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
        self.notify(None, EventType.STREAMUPDATE)
        if stream.stream_type in [StreamType.SOFTWARE, StreamType.DEVICE, StreamType.FILTER]:
            self.notify(None, EventType.DEVICELISTUPDATE)
            
    #add filter   
    def add_filter(self, name: str, filter_type: str, order: float, frequency: float) -> None:
        #WILL CAUSE ISSUE IF FILTERS SHARE THE SAME NAME
        if filterClass(name) not in self.filters:
            #if it does not exist in the filter list, add it to the dictionary
            print('created a filter')
            self.filters[name] = filterClass(name)
        self.filters[name].add_filters('filter', filter_type)
        self.filters[name].add_filters('order', order)
        self.filters[name].add_filters('frequency', frequency)

    def remove_filter(self, name: str) -> None:
        del self.filters[name]

    def get_filter(self, name: str) -> None:
        if name in self.filters.keys():
            return self.filters[name]
        else:
            return None
    
    def remove_dataset(self, name: str) -> None:
        del self.data_sets[name]

    def add_dataset(self, name: str, data_set: ndarray) -> None:
        self.data_sets[name] = data_set
        self.notify(None, EventType.DATASETUPDATE)
        
    def get_dataset(self, name: str) -> ndarray:
        if name in self.data_sets.keys():
            return self.data_sets[name]
        else:
            return None

    

    