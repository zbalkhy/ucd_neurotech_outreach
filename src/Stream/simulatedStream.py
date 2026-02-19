from dataStream import DataStream, StreamType
from common import QUEUE_LENGTH, resource_path
from scipy.io import loadmat
from time import sleep


class SimulatedStream(DataStream):
    def __init__(
        self,
        stream_name: str,
        stream_type: StreamType,
        queue_length: int = QUEUE_LENGTH,
    ):
        super().__init__(stream_name, stream_type, queue_length)
        mat = loadmat(
            resource_path("data.mat"),
            squeeze_me=True,
            struct_as_record=False)
        self.eyesOpen = mat['eyesOpen']
        self.eyesClosed = mat['eyesClosed']

    def _stream(self):
        idx = 0
        n_trials = self.eyesOpen.shape[0]   # shape is (10,250)
        try:
            while not self.shutdown_event.is_set():
                trial = self.eyesOpen[idx]
                self.data.append(trial.tolist())
                idx = (idx + 1) % n_trials
                sleep(1.0)
        except BaseException:
            pass
