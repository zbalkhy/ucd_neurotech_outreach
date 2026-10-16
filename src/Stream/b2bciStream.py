import os
import tempfile
import time
from pathlib import Path
import serial
from serial.tools import list_ports

from Stream.dataStream import DataStream, StreamType
from b2bci.b2bci_client import DeviceSession, StreamConfig
from b2bci.b2bci_reliable import RecordingLink, BatchDecoder, reliable_record


# Espressif native USB, Silicon Labs CP210x, WCH CH340
ESP32_USB_VIDS = {0x303A, 0x10C4, 0x1A86}


def _answers_identify(device: str) -> bool:
    with serial.Serial(device, 460800, timeout=0.5, write_timeout=1) as ser:
        time.sleep(1.5)  # opening the port resets the board; let it boot
        ser.reset_input_buffer()
        ser.write(b"IDENTIFY\n")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if ser.readline().strip() == b"B2BCI_ESP32":
                return True
    return False


def find_b2bci_port() -> str:
    """B2BCI_PORT env var, else the USB port that answers IDENTIFY."""
    port = os.environ.get("B2BCI_PORT")
    if port:
        return port
    for p in list_ports.comports():
        if p.vid not in ESP32_USB_VIDS:  # skips Bluetooth/debug ports
            continue
        try:
            if _answers_identify(p.device):
                return p.device
        except (serial.SerialException, OSError):
            continue
    raise RuntimeError(
        "B2BCI board not found. Check USB and close Serial Monitor.")


def make_tap_link(stream):
    """RecordingLink that also copies verified batches into `stream`."""
    class TapLink(RecordingLink):
        stop_sent = False

        def __init__(self, serial_handle, info):
            super().__init__(serial_handle, info)
            self._decoder = BatchDecoder(
                allow_gaps=info["protocol"] == "ack2")

        def open(self):
            super().open()
            self._decoder.reset()

        def read(self):
            # The recorder turns one KeyboardInterrupt into STOP + drain.
            if stream.shutdown_event.is_set() and not self.stop_sent:
                self.stop_sent = True
                raise KeyboardInterrupt()
            chunk = super().read()
            for kind, event in self._decoder.feed(chunk):
                if kind == "batch":
                    stream.push_rows(event.rows)
            return chunk
    return TapLink


class B2BCIStream(DataStream):
    """8-channel EEG from the B2BCI ESP32 via the ack2 reliable recorder."""

    def __init__(self, com_port, config: StreamConfig,  # com_port None = auto
                 stream_name: str = "B2BCI device",
                 queue_length: int = 500):
        super().__init__(stream_name, StreamType.DEVICE, queue_length)
        self.com_port = com_port
        self.config = config
        self._last_frame = -1

    def get_num_channels(self) -> int:
        # Base heuristic misreads (samples, channels) while fewer than 8
        # samples are buffered; this stream is always 8 channels.
        return 8

    def push_rows(self, rows) -> None:
        # rows are (frame_count, frame_time_ms, ch1..ch8); ACK retransmits
        # repeat frames, so only newer frame counters are kept.
        for row in rows:
            if row[0] > self._last_frame:
                self._last_frame = row[0]
                self.data.append(list(row[2:]))

    def _stream(self) -> None:
        device = None
        try:
            port = self.com_port or find_b2bci_port()  # blocking: stream thread
            device = DeviceSession.connect(
                port, self.config, config_file=None)
            output = Path(tempfile.gettempdir()) / \
                f"b2bci_{time.time_ns()}.csv"
            reliable_record(device.serial, device.info, output,
                            seconds=None, progress=None,
                            link_factory=make_tap_link(self))
        except BaseException as e:
            print(f"[B2BCIStream] {e}")
        finally:
            if device is not None:
                device.close()
