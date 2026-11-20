import zlib
import pytest
import Stream.b2bciStream as mod
from Stream.b2bciStream import (B2BCIStream, StreamState, config_from_form,
                                make_tap_link, find_b2bci_port)
from b2bci.b2bci_client import StreamConfig

SESSION = "0123456789abcdef"


def batch_bytes(frames):
    rows = "".join(
        f"{n},{n * 4}," + ",".join(str(n + c) for c in range(8)) + "\n"
        for n in frames).encode()
    crc = zlib.crc32(rows)
    head = (f"# BATCH {SESSION} {frames[0]} {len(frames)} {len(rows)} "
            f"{crc:08x} {frames[0]}\n").encode()
    return head + rows + f"# END {SESSION} {frames[-1]}\n".encode()


class FakeSerial:
    is_open = True

    def __init__(self, data):
        self.data = data
        self.in_waiting = len(data)

    def read(self, n):
        out, self.data = self.data[:n], self.data[n:]
        self.in_waiting = len(self.data)
        return out


def test_tap_link_fills_deque_and_drops_retransmits():
    stream = B2BCIStream("COMX", StreamConfig("uart"))
    info = {"mode": "uart", "protocol": "ack2"}
    # batch 1-2, the same batch again (ACK retransmit), then batch 3-4
    wire = batch_bytes([1, 2]) + batch_bytes([1, 2]) + batch_bytes([3, 4])
    link = make_tap_link(stream)(FakeSerial(wire), info)
    link.open()
    while link.serial.in_waiting:
        link.read()
    samples = stream.get_stream_data()
    assert samples.shape == (8, 4)          # 8 channels x 4 unique samples
    assert samples[0].tolist() == [1, 2, 3, 4]
    assert stream.get_num_channels() == 8


class FakePort:
    def __init__(self, device, vid):
        self.device, self.vid = device, vid


def test_find_port_skips_non_usb_and_picks_identify_reply(monkeypatch):
    opened = []

    class FakeSer:
        def __init__(self, device, *a, **k):
            self.device = device
            opened.append(device)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def reset_input_buffer(self):
            pass

        def write(self, data):
            assert data == b"IDENTIFY\n"

        def readline(self):
            return b"B2BCI_ESP32\n" if self.device == "/dev/cu.esp" else b""

    monkeypatch.delenv("B2BCI_PORT", raising=False)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(mod.time, "monotonic",
                        iter(range(0, 1000)).__next__)
    monkeypatch.setattr(mod.list_ports, "comports", lambda: [
        FakePort("/dev/cu.Bluetooth-Incoming-Port", None),
        FakePort("/dev/cu.other", 0x10C4),
        FakePort("/dev/cu.esp", 0x303A)])
    monkeypatch.setattr(mod.serial, "Serial", FakeSer, raising=False)
    monkeypatch.setattr(mod.serial, "SerialException", OSError, raising=False)
    assert find_b2bci_port() == "/dev/cu.esp"
    assert "/dev/cu.Bluetooth-Incoming-Port" not in opened


def test_restart_accepts_frames_numbered_from_one_again(monkeypatch):
    stream = B2BCIStream("COMX", StreamConfig("uart"))
    stream.push_rows([(1, 4) + (0.0,) * 8, (2, 8) + (0.0,) * 8])
    assert len(stream.data) == 2
    # second recording: frame counter restarts at 1
    stream._last_frame = 2                     # state left by the first run
    monkeypatch.setattr(mod, "find_b2bci_port", lambda cancel=None: "COMX")
    monkeypatch.setattr(mod.DeviceSession, "connect",
                        staticmethod(lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("no board"))))
    stream._stream()                           # fails to connect, but resets first
    stream.push_rows([(1, 4) + (1.0,) * 8])
    assert len(stream.data) == 1               # old data cleared, new kept


def test_error_ends_in_error_state_and_releases_port(monkeypatch):
    closed = []

    class Dev:
        serial, info = None, {}

        def close(self):
            closed.append(True)

    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(mod, "find_b2bci_port", lambda cancel=None: "COMX")
    monkeypatch.setattr(mod.DeviceSession, "connect",
                        staticmethod(lambda *a, **k: Dev()))
    monkeypatch.setattr(mod, "reliable_record",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("ESP32 recording failed: busy")))
    stream = B2BCIStream(None, StreamConfig("uart"))
    stream._stream()
    assert stream.state == StreamState.ERROR
    assert "busy" in stream.error
    assert closed == [True]            # port released even on failure


def test_stop_before_connect_skips_connect_and_ends_idle(monkeypatch):
    monkeypatch.setattr(mod, "find_b2bci_port", lambda cancel=None: "COMX")

    def must_not_connect(*a, **k):
        raise AssertionError("connect called after stop")
    monkeypatch.setattr(mod.DeviceSession, "connect",
                        staticmethod(must_not_connect))
    stream = B2BCIStream(None, StreamConfig("uart"))
    stream.shutdown_event.set()        # Stop clicked while finding the port
    stream._stream()
    assert stream.state == StreamState.IDLE


@pytest.mark.parametrize("mode,ssid,password,username,command", [
    ("uart", "", "", "", "CONFIG mode=uart port=9000\n"),
    ("personal", "Home", "secret", "",
     "CONFIG mode=personal port=9000 ssid=Home pass=secret\n"),
    ("enterprise", "eduroam", "pw", "me@x.edu",
     "CONFIG mode=enterprise port=9000 ssid=eduroam pass=pw "
     "user=me@x.edu identity=me@x.edu\n"),
])
def test_config_from_form_builds_the_handshake_command(
        mode, ssid, password, username, command):
    assert config_from_form(mode, ssid, password, username).command() == command


@pytest.mark.parametrize("mode,ssid,password,username", [
    ("personal", "My Home", "secret", ""),        # space in network name
    ("enterprise", "eduroam", "", "me@x.edu"),    # enterprise needs a password
    ("bogus", "", "", ""),                        # unknown connection type
])
def test_config_from_form_rejects_bad_input(mode, ssid, password, username):
    with pytest.raises(ValueError):
        config_from_form(mode, ssid, password, username).command()
