from dataStream import *
from eventClass import EventClass, EventType
from filterClass import FilterClass
from featureClass import FeatureClass
from classifier import Classifier
from numpy import ndarray

class UserModel(EventClass):
    def __init__(self):
        self.data_streams: dict = {}
        self.filters: dict = {}
        self.data_sets: dict[str, ndarray] = {}
        self.features: dict[str, FeatureClass] = {}
        self.classifiers: dict[str, Classifier] = {}
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
        if hasattr(self.data_streams, stream.stream_name):
            # stop the stream if it is running
            self.data_streams[stream.stream_name].stop()
            self.data_streams.pop(stream.stream_name)
            print(f"[UserModel] Stream {stream.stream_name} already exists. Overwriting.")
    
        self.data_streams[stream.stream_name] = stream
        self.notify(None, EventType.STREAMUPDATE)
    
    def rename_stream(self, old_name: str, new_name: str) -> bool:
        """Rename a stream from old_name to new_name."""
        if old_name not in self.data_streams:
            print(f"[UserModel] No stream found named {old_name}")
            return False
        if new_name in self.data_streams:
            print(f"[UserModel] A stream named {new_name} already exists")
            return False

        stream: DataStream = self.data_streams.pop(old_name)
        stream.stream_name = new_name
        self.data_streams[new_name] = stream

        print(f"[UserModel] Renamed stream {old_name} to {new_name}")
        self.notify(None, EventType.STREAMUPDATE)
        return True
    
    def remove_stream_by_name(self, name: str) -> bool:
        """Safely remove a stream by its name, stopping any active threads."""
        if name not in self.data_streams:
            print(f"[UserModel] No stream found named {name}")
            return False

        stream: DataStream = self.data_streams.pop(name)
        
        # Gracefully stop the stream thread if it's running
        stream.stop()
        print(f"[UserModel] Removed stream {name}")
        self.notify(None, EventType.STREAMUPDATE)
        return True

    #add filter   
    def add_filter(self, name: str, filter_type: str, order: float, frequency: float) -> None:
        #WILL CAUSE ISSUE IF FILTERS SHARE THE SAME NAME
        if FilterClass(name) not in self.filters:
            #if it does not exist in the filter list, add it to the dictionary
            print('created a filter')
            self.filters[name] = FilterClass(name)
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
    
    def delete_dataset(self, name: str) -> bool:
        if name in self.data_sets.keys():
            del self.data_sets[name]
            self.notify(None, EventType.DATASETUPDATE)
            return True
        else:
            return False
    
    def add_dataset(self, name: str, data_set: ndarray) -> None:
        self.data_sets[name] = data_set
        self.notify(None, EventType.DATASETUPDATE)
        
    def get_dataset(self, name: str) -> ndarray:
        if name in self.data_sets.keys():
            return self.data_sets[name]
        else:
            return None
        
    def rename_dataset(self, old_name: str, new_name: str) -> bool:
        """Rename a dataset from old_name to new_name."""
        if old_name not in self.data_sets:
            print(f"[UserModel] No dataset found named {old_name}")
            return False
        if new_name in self.data_sets:
            print(f"[UserModel] A dataset named {new_name} already exists")
            return False

        data_set = self.data_sets.pop(old_name)
        self.data_sets[new_name] = data_set

        print(f"[UserModel] Renamed dataset {old_name} to {new_name}")
        self.notify(None, EventType.DATASETUPDATE)
        return True
    
    def get_datasets(self) -> dict[str, ndarray]:
        return self.data_sets
    
    def get_features(self) -> dict[str, FeatureClass]:
        return self.features
    
    def add_feature(self, feature: FeatureClass) -> None:
        self.features[str(feature)] = feature

    def remove_classifier(self, name: str) -> bool:
        if name in self.classifiers.keys():
            del self.classifiers[name]
            self.notify(None, EventType.CLASSIFIERUPDATE)
            return True
        else:
            return False

    def add_classifier(self, name: str, classifier: Classifier) -> None:
        self.classifiers[name] = classifier
        self.notify(None, EventType.CLASSIFIERUPDATE)
        
    def get_classifier(self, name: str) -> Classifier:
        if name in self.classifiers.keys():
            return self.classifiers[name]
        else:
            return None
    
    def get_classifiers(self) -> dict[str, Classifier]:
        return self.classifiers

    def rename_classifier(self, old_name: str, new_name: str) -> bool:
        """Rename a classifier from old_name to new_name."""
        if old_name not in self.classifiers:
            print(f"[UserModel] No classifier found named {old_name}")
            return False
        if new_name in self.classifiers:
            print(f"[UserModel] A classifier named {new_name} already exists")
            return False

        classifier = self.classifiers.pop(old_name)
        self.classifiers[new_name] = classifier

        print(f"[UserModel] Renamed classifier {old_name} to {new_name}")
        self.notify(None, EventType.CLASSIFIERUPDATE)
        return True
    

    