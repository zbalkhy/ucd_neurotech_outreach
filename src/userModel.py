from dataStream import *
from threading import Lock
from eventClass import EventClass, EventType
from filterClass import filterClass

class UserModel(EventClass):
    def __init__(self):
        self.data_streams: dict = {}
        self.filters: list = []
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
    def add_filter(self, name, filter_type, order, frequency) -> None:
        #WILL CAUSE ISSUE IF FILTERS SHARE THE SAME NAME
        if filterClass(name) not in self.filters:
            
            #if it does not exist in the filter list, add it to the list
            print('created a filter')
            self.filters.append(filterClass(name))
        for filter_name in self.filters:
            if filter_name.filter_name == name:
                print('added onto a filter')
                #sweep through the list and add filters
                filter_name.add_filters('filter', filter_type)
                filter_name.add_filters('order', order)
                filter_name.add_filters('frequency', frequency)

    def remove_filter(self, position) -> None:
        del self.filters['filter'][position]
        del self.filters['order'][position]
        del self.filters['frequency'][position]


    

    