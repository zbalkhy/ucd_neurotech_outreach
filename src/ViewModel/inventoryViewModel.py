from Models.userModel import UserModel
from Stream.deviceStream import DeviceStream
from common import RETRY_SEC
from Stream.dataStream import DataStream, StreamType
from Classes.eventClass import EventType
from Stream.composedStream import ComposedStream
from Stream.xrpControlStream import XRPControlStream


class InventoryViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def toggle_stream(self, stream_name) -> None:
        stream = self.user_model.get_stream(stream_name)
        if stream is None:
            print(f'[Inventory] No stream found named {stream_name}')
            return
        if stream.is_alive():
            stream.stop()
            print('[Inventory] stopping stream')
        else:
            stream.start()
            print('[Inventory] starting stream')
        self.user_model.notify(stream_name, EventType.STREAMTOGGLED)

    def train_classifier(self, name: str) -> None:
        classifier = self.user_model.get_classifier(name)
        classifier.train_model()
        self.user_model.add_classifier(name, classifier)
        self.add_classifier_stream(name)

    def add_classifier_stream(self, name: str) -> None:
        # this will need a major refactor, this is hacky, dont use this
        openbci = self.user_model.get_stream('openbci')
        classifier = self.user_model.get_classifier(name)
        classifier_stream = ComposedStream(
            openbci, [classifier], name + "_stream", StreamType.CONTROL, 1)
        self.user_model.add_stream(classifier_stream)

        xrp_stream = XRPControlStream(
            classifier_stream,
            "/dev/tty.usbmodem1301",
            9600,
            1,
            "xrp",
            StreamType.DEVICE,
            100)
        self.user_model.add_stream(xrp_stream)

    def get_stream_names(self) -> list[str]:
        stream_names = []
        for stream in self.user_model.get_streams():
            stream_names.append(stream.stream_name)
        return stream_names

    def get_dataset_names(self) -> list[str]:
        return list(self.user_model.get_datasets().keys())

    def get_classifier_names(self) -> list[str]:
        return list(self.user_model.get_classifiers().keys())

    def delete_dataset_by_name(self, name: str) -> bool:
        return self.user_model.delete_dataset(name)

    def delete_stream_by_name(self, name: str) -> bool:
        return self.user_model.remove_stream_by_name(name)

    def delete_classifier_by_name(self, name: str) -> bool:
        return self.user_model.remove_classifier(name)

    def rename_stream(self, old_name: str, new_name: str) -> bool:
        return self.user_model.rename_stream(old_name, new_name)

    def rename_dataset(self, old_name: str, new_name: str) -> bool:
        return self.user_model.rename_dataset(old_name, new_name)

    def rename_classifier(self, old_name: str, new_name: str) -> bool:
        return self.user_model.rename_classifier(old_name, new_name)
