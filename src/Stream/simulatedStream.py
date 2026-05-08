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
        idx_open = 0
        idx_closed = 0
        n_open = self.eyesOpen.shape[0]   # shape is (10,250)
        n_closed = self.eyesClosed.shape[0]
        use_open = True

        try:
            while not self.shutdown_event.is_set():
                if use_open:
                    trial = self.eyesOpen[idx_open]
                    idx_open = (idx_open + 1) % n_open
                else:
                    trial = self.eyesClosed[idx_closed]
                    idx_closed = (idx_closed + 1) % n_closed

                self.data.append(trial.tolist())
                use_open = not use_open
                sleep(1.0)

        except BaseException:
            pass
