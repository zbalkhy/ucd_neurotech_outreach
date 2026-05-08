import numpy as np


class NearestMean():
    def __init__(self):
        self.means = []
        self.stds = []
        self.unique_labels = None

    def fit(self, features: np.ndarray, labels: np.ndarray):
        self.unique_labels, indices = np.unique(labels, return_inverse=True)
        for x in self.unique_labels:
            # create list with means and standard deviations
            # the weird things is to make sure labels are independent of their
            # idx
            self.means.append(
                features[:, (indices == sum(np.where(self.unique_labels == x)))].mean(axis=1))
            self.stds.append(
                features[:, (indices == sum(np.where(self.unique_labels == x)))].std(axis=1))

    def predict(self, features: np.ndarray):
        distance = []
        for mean_var, std_var in zip(self.means, self.stds):
            # for each label (corresponding to index in list)
            # determine euclidian distance for each feature (normalized to
            # standard deviation)
            distance.append(
                np.linalg.norm(
                    (features.T - mean_var) / std_var,
                    axis=1))
        # turns distance into numpy array,
        # finds the minimum position (corresponds to label idx)
        # sets to label index for correct label
        return self.unique_labels[np.array(distance).argmin(axis=0)]
