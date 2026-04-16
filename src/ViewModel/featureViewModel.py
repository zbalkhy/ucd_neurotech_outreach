from Models.userModel import UserModel
import numpy as np
from Classes.featureClass import FeatureClass


class FeatureViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def get_datasets(self) -> dict[str, np.ndarray]:
        return self.user_model.get_datasets()

    def get_dataset(self, name: str) -> np.ndarray:
        return self.user_model.get_dataset(name)

    def get_dataset_names(self) -> list[str]:
        return list(self.user_model.get_datasets().keys())

    def get_features(self) -> dict[str, FeatureClass]:
        return self.user_model.get_features()

    def get_feature_names(self) -> list[str]:
        return list(self.user_model.get_features().keys())

    def get_feature(self, name: str) -> FeatureClass:
        return self.user_model.get_features()[name]

    def calc_feature_datasets(self,
                              feature_names: list[str],
                              dataset_names: list[str],
                              channels: list[int]) -> tuple[list[str],
                                                            list[np.ndarray]]:
        # get feature and dataset
        features = [self.get_feature(feature) for feature in feature_names]
        datasets = [self.get_dataset(dataset) for dataset in dataset_names]

        # calculate feature on dataset
        feature_datasets = []
        labels = []
        for i, feature in enumerate(features):
            for j, dataset in enumerate(datasets):
                feature_dataset = []
                for k in range(dataset.shape[0]):
                    trial = dataset[k, :]
                    trial_feature = feature.apply(trial, 128)
                    # TODO: introduce channel selection in the ui and pass down to here
                    # for now take first channel
                    feature_dataset.append(trial_feature)
                feature_datasets.append(np.array(feature_dataset))
                labels.append(feature_names[i] + "_" + dataset_names[j])
        return labels, feature_datasets
