from typing import Dict, List, Tuple
import numpy as np
from Classes.featureClass import FeatureClass
from Classes.filterClass import FilterClass
from sklearn.linear_model import LogisticRegression
from common import SAMPLING_FREQ
import joblib
import os

MODEL_SAVE_DIR = 'user_classifiers'


class Classifier:
    def __init__(
        self,
        label0_datasets: Dict[str, np.ndarray] = None,
        label1_datasets: Dict[str, np.ndarray] = None,
        features: List[FeatureClass] = None,
        filters: List[FilterClass] = None,
        model=None
    ):
        self.label0_datasets: Dict[str,
                                   np.ndarray] = label0_datasets if label0_datasets is not None else {}
        self.label1_datasets: Dict[str,
                                   np.ndarray] = label1_datasets if label1_datasets is not None else {}
        self.features: List[FeatureClass] = features if features is not None else [
        ]
        self.filters: List[FilterClass] = filters if filters is not None else []
        self.model = model

    # -----------------------
    # Datasets
    # -----------------------
    def add_dataset(self, label: int, name: str, data: np.ndarray) -> None:
        if label == 0:
            self.label0_datasets[name] = data
        elif label == 1:
            self.label1_datasets[name] = data
        else:
            raise ValueError("Label must be 0 or 1.")

    def get_dataset(self, label: int, name: str) -> np.ndarray | None:
        if label == 0:
            return self.label0_datasets.get(name, None)
        elif label == 1:
            return self.label1_datasets.get(name, None)
        else:
            raise ValueError("Label must be 0 or 1.")

    def get_datasets(self, label: int) -> Dict[str, np.ndarray]:
        if label == 0:
            return self.label0_datasets
        elif label == 1:
            return self.label1_datasets
        else:
            raise ValueError("Label must be 0 or 1.")

    # -----------------------
    # Features
    # -----------------------
    def add_feature(self, feature: FeatureClass) -> None:
        self.features.append(feature)

    def get_features(self) -> List[FeatureClass]:
        return self.features

    # -----------------------
    # Filters
    # -----------------------
    def add_filter(self, f: FilterClass) -> None:
        self.filters.append(f)

    def get_filters(self) -> List[FilterClass]:
        return self.filters

    # -----------------------
    # Training
    # -----------------------
    def generate_features(self, data: np.ndarray) -> np.ndarray:
        # apply filters
        for flt in self.filters:
            data = flt.apply(data, SAMPLING_FREQ)

        # extract features per channel
        feature_vectors = []
        for feature in self.features:
            # TODO: instead of hard-coding SAMPLING_FREQ, have the Features class
            # extract it as metadata from the data (maybe have a data wrapper)
            feature_vals = feature.apply(
                data, SAMPLING_FREQ)  # shape: (channels,)
            feature_vectors.append(feature_vals)

        # flatten into single vector
        return feature_vectors  # np.concatenate(feature_vectors, axis=0)

    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []

        for _, data in self.label0_datasets.items():
            for i in range(data.shape[0]):
                X.append(self.generate_features(data[i, :]))
                y.append(0)

        for _, data in self.label1_datasets.items():
            for i in range(data.shape[0]):
                X.append(self.generate_features(data[i, :]))
                y.append(1)

        return np.array(X), np.array(y)

    def train_model(self) -> None:
        X, y = self.prepare_training_data()
        self.model = LogisticRegression(
            random_state=0
        )
        self.model.fit(np.array(X).reshape(-1, 1), y)

    # -----------------------
    # Prediction
    # -----------------------
    def predict_sample(self, sample: np.ndarray) -> int:
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        features = np.array(self.generate_features(sample)).reshape(1, -1)
        prediction = (features[0] < 7e-7)
        # prediction = self.model.predict(features)
        return int(prediction)

    def apply(self, data: np.ndarray, fs: int) -> np.ndarray:
        prediction = self.predict_sample(data)
        print(prediction)
        if prediction:
            return np.array(['eyesOpen'])
        else:
            return np.array(['eyesClosed'])

    def to_dict(self) -> dict:
        model_filename = None
        if self.model:
            model_filename = f'{self.model.__class__.__name__}.joblib'
            if not os.path.exists(MODEL_SAVE_DIR):
                os.makedirs(MODEL_SAVE_DIR)
            joblib.dump(
                self.model,
                os.path.join(
                    MODEL_SAVE_DIR,
                    model_filename))
        return {
            'label0_datasets': {k: v.tolist() for k, v in self.label0_datasets.items()},
            'label1_datasets': {k: v.tolist() for k, v in self.label1_datasets.items()},
            'features': [f.to_dict() for f in self.features],
            'filters': [f.to_dict() for f in self.filters],
            'model_filename': model_filename
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Classifier':

        label0_datasets = {
            k: np.array(v) for k,
            v in data['label0_datasets'].items()}
        label1_datasets = {
            k: np.array(v) for k,
            v in data['label1_datasets'].items()}
        features = [FeatureClass.from_dict(f) for f in data['features']]
        filters = [FilterClass.from_dict(f) for f in data['filters']]
        model = None
        if data.get('model_filename'):
            model_path = os.path.join(MODEL_SAVE_DIR, data['model_filename'])
            if os.path.exists(model_path):
                model = joblib.load(model_path)
            else:
                print(f"Warning: Model file {model_path} not found.")

        return cls(
            label0_datasets=label0_datasets,
            label1_datasets=label1_datasets,
            features=features,
            filters=filters,
            model=model
        )
