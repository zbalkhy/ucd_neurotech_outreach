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

    # Store incoming data in a list for any amount of channels
    def make_channels_list(sample):
        try:
            return [float(sample)]

        except TypeError:
            return [float(n) for n in sample]

    def _stream(self):
        # shape is (10,250) --> (10 trials, 250 samples)
        n_trials = [self.eyesOpen.shape[0], self.eyesClosed.shape[0]]
        sources = [self.eyesOpen, self.eyesClosed]
        source_type = 0  # 0 for eyesOpen trial, 1 for eyesClosed trial
        trial_idx = [0, 0]
        dt = 1 / 250  # Sampling at 250 Hz(?)

        try:
            while not self.shutdown_event.is_set():
                trial = sources[source_type][trial_idx[source_type]]

                for sample in trial:
                    self.data.append(self.make_channels_list(sample))
                    sleep(dt)

                trial_idx[source_type] = (
                    trial_idx[source_type] + 1) % n_trials[source_type]
                source_type = 0 if source_type else 1

        except BaseException:
            pass
