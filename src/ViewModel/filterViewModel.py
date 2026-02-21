from Models.userModel import UserModel
from Stream.dataStream import StreamType
from Stream.composedStream import ComposedStream


class filterViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    # add new filter to the user model
    def add_filter(self, name, filter_type, order, frequency) -> None:
        self.user_model.add_filter(name, filter_type, order, frequency)

    # remove filter based on the position
    def remove_filter(self, position) -> None:
        self.user_model.remove_filter(position)

    def get_filter(self):
        return self.user_model.filters()

    def get_streams(self):
        return self.user_model.get_streams()

    # create filter stream
    def create_filter_stream(
            self,
            name: str,
            reference_stream_name: str) -> None:
        # currently the filter and the filtered stream will be named the same
        # thing
        filter_obj = self.user_model.get_filter(name)
        filtered_stream = ComposedStream(self.user_model.get_stream(
            reference_stream_name), [filter_obj], name, StreamType.FILTER, 250)
        self.user_model.add_stream(filtered_stream)
