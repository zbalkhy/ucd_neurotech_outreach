from userModel import UserModel
from deviceStream import DeviceStream
from common import RETRY_SEC
from dataStream import DataStream

class EegDeviceViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    # add new device to the user model
    def connect_device(self, IP_address: str, port: int):
        new_device = DeviceStream(IP_address, port, RETRY_SEC, self.user_model)  
        self.user_model.add_stream(new_device)
        new_device.start()
    
    def get_devices(self) -> list[DataStream]:
        return self.user_model.get_streams()