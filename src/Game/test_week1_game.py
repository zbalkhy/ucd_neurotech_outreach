"""Interactive demo; run directly, never as an automated test."""

import sys
from pathlib import Path
from time import sleep
import tkinter as tk

import scipy.io as sio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    from Classes.classifierClass import Classifier
    from Classes.featureClass import FeatureClass, FeatureType
    from Models.userModel import UserModel
    from Stream.composedStream import ComposedStream
    from Stream.dataStream import StreamType
    from Stream.gameControlStream import MatFileStream
    from View.runnerView import RunnerView
    from ViewModel.runnerViewModel import RunnerViewModel

    mat_path = Path(__file__).resolve().parents[1] / "data.mat"
    data = sio.loadmat(mat_path)
    classifier = Classifier(
        features=[FeatureClass(FeatureType.ALPHA)],
        label0_datasets={'eyesClosed': data['eyesClosed']},
        label1_datasets={'eyesOpen': data['eyesOpen']})
    classifier.train_model()
    eeg_stream = MatFileStream(mat_path, queue_length=250)
    classification_stream = ComposedStream(
        eeg_stream, [classifier], "Brain state", StreamType.CONTROL, 1)
    user_model = UserModel()
    user_model.add_stream(eeg_stream)
    user_model.add_stream(classification_stream)
    root = None
    view = None
    try:
        eeg_stream.start()
        # Let the classifier's source collect a full training-sized window.
        while len(eeg_stream.data) < 250:
            if not eeg_stream.is_alive():
                raise RuntimeError("EEG demo source stopped")
            sleep(0.05)
        classification_stream.start()
        root = tk.Tk()
        view_model = RunnerViewModel(user_model)
        view_model.select_mode("label")
        view_model.select_source(classification_stream)
        view = RunnerView(root, view_model)
        root.mainloop()
    finally:
        if view is not None:
            view.on_close()
        classification_stream.stop()
        eeg_stream.stop()


if __name__ == "__main__":
    main()
