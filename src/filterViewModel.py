from userModel import UserModel
from deviceStream import DeviceStream
from common import RETRY_SEC
from dataStream import DataStream, StreamType
from filteredSoftwareStream import FilteredStream

class filterViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    #add new filter to the user model
    def add_filter(self, name, filter_type, order, frequency) -> None:
        self.user_model.add_filter(name, filter_type, order, frequency)

    #remove filter based on the position
    def remove_filter(self, position) -> None:
        self.user_model.remove_filter(position)

    def get_filter(self):
        return self.user_model.filters()

    def get_streams(self):
        return self.user_model.get_streams()
    #create filter stream
    def create_filter_stream(self, name, reference_stream) -> None:
        filtered_stream = FilteredStream(str(reference_stream), name, StreamType.FILTER, self.user_model, self.user_model.filters)
        self.user_model.add_stream(filtered_stream)
        