from typing import Dict, List, Tuple
import numpy as np
from featureClass import FeatureClass
from filterClass import FilterClass
from sklearn.linear_model import LogisticRegression
from common import SAMPLING_FREQ

class Classifier:
    def __init__(
        self,
        label0_datasets: Dict[str, np.ndarray] = None,
        label1_datasets: Dict[str, np.ndarray] = None,
        features: List[FeatureClass] = None,
        filters: List[FilterClass] = None
    ):
        self.label0_datasets: Dict[str, np.ndarray] = label0_datasets if label0_datasets is not None else {}
        self.label1_datasets: Dict[str, np.ndarray] = label1_datasets if label1_datasets is not None else {}
        self.features: List[FeatureClass] = features if features is not None else []
        self.filters: List[FilterClass] = filters if filters is not None else []
        self.model = None

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
            data = flt.apply(data)

        # extract features per channel
        feature_vectors = []
        for feature in self.features:
            # TODO: instead of hard-coding SAMPLING_FREQ, have the Features class  
            #       extract it as metadata from the data (maybe have a data wrapper)
            feature_vals = feature.apply(data, SAMPLING_FREQ)  # shape: (channels,)
            feature_vectors.append(feature_vals)

        # flatten into single vector
        return np.concatenate(feature_vectors, axis=0)

    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []

        for _, data in self.label0_datasets.items():
            X.append(self.generate_features(data))
            y.append(0)

        for _, data in self.label1_datasets.items():
            X.append(self.generate_features(data))
            y.append(1)

        return np.array(X), np.array(y)

    def train_model(self) -> None:
        X, y = self.prepare_training_data()
        self.model = LogisticRegression(
            solver="liblinear",
            max_iter=1000,
            random_state=42
        )
        self.model.fit(X, y)

    # -----------------------
    # Prediction
    # -----------------------
    def predict_sample(self, sample: np.ndarray) -> int:
        if self.model is None:
            raise RuntimeError("Model not trained yet.")
        features = self.prepare_training_data(sample).reshape(1, -1)
        prediction = self.model.predict(features)
        return int(prediction)
