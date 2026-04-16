from Stream.dataStream import *
from pylsl import StreamInlet, StreamInfo


class LslStream(DataStream):
    def __init__(self, stream: StreamInfo, fs: int,
                 stream_name: str,
                 stream_type: StreamType,
                 queue_length: int = QUEUE_LENGTH):
        self.stream = stream
        self.fs = fs
        super().__init__(stream_name, stream_type, queue_length)

    def _stream(self) -> None:
        try:
            # create a new inlet to read from the stream
            inlet = StreamInlet(self.stream)
            while not self.shutdown_event.is_set():
                # get a new sample (you can also omit the timestamp part if you're not
                # interested in it)
                sample, timestamp = inlet.pull_sample()

                # add time correction to get system local time, and append
                # timestamp to data
                timestamp = timestamp + inlet.time_correction()
                if sample:
                    sample.append(timestamp)
                    try:
                        self.data.append(sample[0])
                    except BaseException:
                        pass

        except Exception as e:
            print(e)
