from userModel import UserModel
from deviceStream import DeviceStream
from common import RETRY_SEC
from dataStream import DataStream, StreamType
from eventClass import EventType

class EEGDeviceViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    # add new device to the user model
    def add_device(self, IP_address: str, port: int, name: str) -> None:
        new_device = DeviceStream(IP_address, port, RETRY_SEC, name, StreamType.DEVICE)  
        self.user_model.add_stream(new_device)

    def toggle_device_stream(self, device_name) -> None:
        if device_name in self.get_device_names():
            stream = self.user_model.get_stream(device_name)
            if stream.is_alive():
                stream.stop()
                print('stopping stream')
            else:
                stream.start()
                print('starting stream')
            self.user_model.notify(device_name, EventType.STREAMTOGGLED)

    #temporary fix to have the streams put in the devices category
    def get_devices(self) -> list[DataStream]:
        devices = []
        for stream in self.user_model.get_streams():
            if stream.stream_type in [StreamType.DEVICE, StreamType.SOFTWARE, StreamType.FILTER, StreamType.CONTROL]:
                devices.append(stream)
        return devices

    def get_device_names(self) -> list[str]:
        device_names = []
        for stream in self.user_model.get_streams():
            if stream.stream_type in [StreamType.DEVICE, StreamType.SOFTWARE, StreamType.FILTER, StreamType.CONTROL]:
                device_names.append(stream.stream_name)
        return device_names