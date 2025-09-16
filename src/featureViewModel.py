from userModel import UserModel
import numpy as np 
from featureClass import FeatureClass

class FeatureViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def get_datasets(self) -> dict[str, np.ndarray]:
        return self.user_model.get_datasets()

    def get_dataset(self, name: str) -> np.ndarray:
        return self.user_model.get_dataset(name)
    
    def get_dataset_names(self) ->list[str]:
        return list(self.user_model.get_datasets().keys())
    
    def get_features(self) -> dict[str, FeatureClass]:
        return self.user_model.get_features()
    
    def get_feature_names(self) -> list[str]:
        return list(self.user_model.get_features().keys())
    
    def get_feature(self, name: str) -> FeatureClass:
        return self.user_model.get_features()[name]
    
    def calc_feature_datasets(self, feature_name: str, dataset_names: list[str]) -> list[np.ndarray]:
        # calculate feature on dataset
        feature = self.get_feature(feature_name)
        datasets = [self.get_dataset(dataset) for dataset in dataset_names]
        
        feature_datasets = []
        for dataset in datasets:
            feature_dataset = []
            for i in range(dataset.shape[2]):
                trial = dataset[:,:,i]
                trial_feature = feature.apply(trial, 128)
                ##TODO: introduce channel selection in the ui and pass down to here
                feature_dataset.append(trial_feature[0]) # for now take first channel
            feature_datasets.append(np.array(feature_dataset))
        return feature_datasets