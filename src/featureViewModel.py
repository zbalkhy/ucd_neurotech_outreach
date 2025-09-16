from userModel import UserModel
from numpy import ndarray
from featureClass import FeatureClass

class FeatureViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def get_datasets(self) -> dict[str, ndarray]:
        return self.user_model.get_datasets()

    def get_dataset(self, name: str) -> ndarray:
        return self.user_model.get_dataset(name)
    
    def get_dataset_names(self) ->list[str]:
        return list(self.user_model.get_datasets().keys())
    
    def get_features(self) -> dict[str, FeatureClass]:
        return self.user_model.get_features()
    
    def get_feature_names(self) -> list[str]:
        return list(self.user_model.get_features().keys())
    
    def get_feature(self, name: str) -> FeatureClass:
        return self.user_model.get_features()[name]