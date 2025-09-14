from userModel import UserModel
from numpy import ndarray

class FeatureViewModel(object):
    def __init__(self, user_model: UserModel):
        self.user_model: UserModel = user_model

    def get_datasets(self) -> dict[str, ndarray]:
        return self.user_model.get_datasets()

    def get_dataset_names(self) ->list[str]:
        return self.user_model.get_datasets().keys()