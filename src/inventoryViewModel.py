from userModel import UserModel
from deviceStream import DeviceStream
from common import RETRY_SEC
from dataStream import DataStream, StreamType
from eventClass import EventType

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

    def get_stream_names(self) -> list[str]:
        stream_names = []
        for stream in self.user_model.get_streams():
            stream_names.append(stream.stream_name)
        return stream_names
    
    def get_dataset_names(self) -> list[str]:
        dataset_names = []
        for name in self.user_model.get_datasets().keys():
            dataset_names.append(name)
        return dataset_names
    
    def delete_dataset_by_name(self, name: str) -> bool:
        return self.user_model.delete_dataset(name)
    
    def delete_stream_by_name(self, name: str) -> bool:
        return self.user_model.remove_stream_by_name(name)
    
    def rename_stream(self, old_name: str, new_name: str) -> bool:
        return self.user_model.rename_stream(old_name, new_name)
    
    def rename_dataset(self, old_name: str, new_name: str) -> bool:
        return self.user_model.rename_dataset(old_name, new_name)