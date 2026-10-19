from time import monotonic

from Stream.dataStream import DataStream, StreamType
from common import QUEUE_LENGTH, resource_path
from scipy.io import loadmat

SAMPLE_RATE = 250      # Hz, matches the plotter's sampling rate
CHUNK_INTERVAL = 0.04  # push a small chunk every 40 ms (10 samples)


class SimulatedStream(DataStream):
    """
    Plays back recorded trials from data.mat as a continuous sample stream,
    alternating eyesOpen / eyesClosed trials at SAMPLE_RATE.
    """
    

    # Label of the trial currently being played (None until started)
    currentTrialType = None

    def __init__(
        self,
        stream_name: str,
        stream_type: StreamType,
        queue_length: int = QUEUE_LENGTH,
        BUFFER_SAMPLES = 250   # same 1 s window as the software stream
           # 2 s at 250 Hz, matches the plotter's window
    ):
        super().__init__(stream_name, stream_type, BUFFER_SAMPLES)
        mat = loadmat(
            resource_path("src/data.mat"),
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
        samples_per_chunk = max(1, int(SAMPLE_RATE * CHUNK_INTERVAL))

        # Start each playback fresh
        self.data.clear()
        self.currentTrialType = None

        start = monotonic()
        sent = 0

        try:
            while not self.shutdown_event.is_set():
                if use_open:
                    trial = self.eyesOpen[idx_open]
                    idx_open = (idx_open + 1) % n_open
                    label = "eyesOpen"
                else:
                    trial = self.eyesClosed[idx_closed]
                    idx_closed = (idx_closed + 1) % n_closed
                    label = "eyesClosed"
                use_open = not use_open

                # Label matches the samples being pushed from here on
                self.currentTrialType = label
                samples = trial.tolist()

                for i in range(0, len(samples), samples_per_chunk):
                    chunk = samples[i:i + samples_per_chunk]
                    self.data.extend(chunk)
                    sent += len(chunk)

                    # Keep a steady real-time rate (no drift), and wake
                    # immediately if stop() is called.
                    delay = start + sent / SAMPLE_RATE - monotonic()
                    if delay > 0 and self.shutdown_event.wait(delay):
                        return
                    if self.shutdown_event.is_set():
                        return

        except Exception as e:
            print(f"[SimulatedStream] stopped on error: {e}")

    # A recording is a single channel
    def get_num_channels(self) -> int:
        return 1