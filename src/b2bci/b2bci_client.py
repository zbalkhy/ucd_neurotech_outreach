"""USB setup and one eight-channel CSV recorder for all B2BCI stream modes."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import deque
import csv
import json
import math
import re
import time

BAUD = 460800
CHANNELS = [f"ch{i}_uV" for i in range(1, 9)]
CSV_COLUMNS = ["frame_count", "frame_time_ms", *CHANNELS]


@dataclass
class StreamConfig:
    mode: str = "uart"
    ssid: str = ""
    password: str = field(default="", repr=False)
    port: int = 9000
    username: str = ""
    identity: str = ""

    def command(self):
        mode = self.mode.lower()
        if mode == "esp32":
            mode = "ap"
        if mode not in ("uart", "ap", "personal", "enterprise"):
            raise ValueError("Mode must be uart, ap, personal, or enterprise.")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise ValueError("TCP port must be an integer from 1 to 65535.")
        fields = {"mode": mode, "port": str(self.port)}
        if mode != "uart":
            if not 1 <= len(self.ssid.encode("utf-8")) <= 32:
                raise ValueError("SSID must contain 1 to 32 UTF-8 bytes.")
            fields.update(ssid=self.ssid, **{"pass": self.password})
        if mode == "ap" and not 8 <= len(self.password.encode("utf-8")) <= 63:
            raise ValueError("AP password must contain 8 to 63 UTF-8 bytes.")
        if mode == "enterprise":
            if not self.username or not self.password:
                raise ValueError("Enterprise mode needs a username and password.")
            fields.update(user=self.username, identity=self.identity or self.username)
        for name, value in fields.items():
            if any(c.isspace() for c in value) or "\x00" in value:
                raise ValueError(f"{name} cannot contain whitespace or NUL with this handshake.")
        command = "CONFIG " + " ".join(f"{k}={v}" for k, v in fields.items()) + "\n"
        if len(command.encode("utf-8")) > 511:
            raise ValueError("Configuration command exceeds firmware's 511-byte limit.")
        return command


class LineBuffer:
    """Reassemble serial/TCP chunks without losing split or combined CSV rows."""
    def __init__(self):
        self.pending = bytearray()

    def feed(self, chunk):
        self.pending.extend(chunk)
        lines = []
        while True:
            end = self.pending.find(b"\n")
            if end < 0:
                break
            if end > 4096:
                raise ValueError("Incoming line exceeds 4096 bytes.")
            lines.append(bytes(self.pending[:end]).strip())
            del self.pending[:end + 1]
        if len(self.pending) > 4096:
            raise ValueError("Incoming stream has no valid line boundaries.")
        return lines


def parse_state(line):
    if isinstance(line, bytes):
        line = line.decode("utf-8", "replace")
    if not line.startswith(("OK ready ", "OK status ")):
        return None
    return dict(token.split("=", 1) for token in line.split()[2:] if "=" in token)


def parse_frame(line):
    if isinstance(line, bytes):
        line = line.decode("ascii")
    line = line.strip()
    if not line or line.startswith(("#", "OK ", "ERR ", "frame_count,")):
        return None
    parts = line.split(",")
    if len(parts) != 10:
        raise ValueError("Expected frame_count, frame_time_ms and exactly 8 channels.")
    frame, timestamp = int(parts[0]), int(parts[1])
    values = [float(value) for value in parts[2:]]
    if not 0 <= frame <= 0xFFFFFFFF or not 0 <= timestamp <= 0xFFFFFFFF:
        raise ValueError("Frame number/timestamp is outside uint32 range.")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Non-finite channel value.")
    return [frame, timestamp, *values]


@dataclass
class CaptureStats:
    samples: int = 0
    dropped_frames: int = 0
    bad_lines: int = 0
    duplicates: int = 0
    last_frame: int | None = None

    def accept(self, frame):
        if self.last_frame is not None:
            delta = (frame - self.last_frame) & 0xFFFFFFFF
            if delta == 0:
                self.duplicates += 1
                return False
            if delta >= 0x80000000:
                raise RuntimeError("Device frame counter restarted. Begin a new recording.")
            self.dropped_frames += delta - 1
        self.last_frame = frame
        self.samples += 1
        return True


def capture_csv(read_chunk, output, seconds=30, idle_timeout=5, progress=print):
    """Record one connection; preserve a partial CSV on interruption/failure."""
    if seconds is not None and seconds <= 0:
        raise ValueError("seconds must be positive or None.")
    output = Path(output)
    stats = CaptureStats()
    lines = LineBuffer()
    start = last_sample = last_report = time.monotonic()
    created = False
    try:
        with output.open("x", newline="", encoding="utf-8") as handle:
            created = True
            writer = csv.writer(handle)
            writer.writerow(CSV_COLUMNS)
            try:
                while seconds is None or time.monotonic() - start < seconds:
                    chunk = read_chunk()
                    for line in lines.feed(chunk):
                        try:
                            row = parse_frame(line)
                        except (ValueError, UnicodeError):
                            stats.bad_lines += 1
                            continue
                        if row is None:
                            continue
                        if stats.accept(row[0]):
                            writer.writerow(row)
                            last_sample = time.monotonic()
                    now = time.monotonic()
                    if now - last_sample >= idle_timeout:
                        raise TimeoutError(f"No valid eight-channel samples for {idle_timeout:g} seconds. Check firmware/mode.")
                    if now - last_report >= 1:
                        if progress:
                            progress(f"samples={stats.samples} | received={stats.samples / (now-start):.1f} Hz | "
                                     f"dropped={stats.dropped_frames} | bad_lines={stats.bad_lines}")
                        handle.flush()
                        last_report = now
            except KeyboardInterrupt:
                if progress:
                    progress("Recording stopped; collected samples saved.")
    except Exception:
        if progress and created:
            progress(f"Recording failed; partial file preserved at {output.resolve()}")
        raise
    if progress:
        progress(f"Saved {stats.samples} samples to {output.resolve()}")
    return stats


class DeviceSession:
    """Keep USB open across setup and recording to avoid reopening/resetting it."""
    def __init__(self, serial_handle, info):
        self.serial = serial_handle
        self.info = info

    @classmethod
    def connect(cls, com_port, config=None, *, provision=True, timeout=30,
                config_file="esp_last.json", serial_factory=None, boot_delay=1.2):
        command = config.command() if provision and config is not None else "STATUS\n"
        if provision and config is None:
            raise ValueError("Provide a StreamConfig when provision=True.")
        if serial_factory is None:
            import serial
            serial_factory = serial.Serial
        ser = serial_factory(com_port, BAUD, timeout=0.25, write_timeout=2)
        try:
            time.sleep(boot_delay)
            ser.reset_input_buffer()
            ser.write(command.encode("utf-8"))
            lines = LineBuffer()
            saved = not provision
            deadline = time.monotonic() + timeout
            last_query = time.monotonic()
            info = None
            replies = deque(maxlen=12)
            while time.monotonic() < deadline:
                for line in lines.feed(ser.read(ser.in_waiting or 1)):
                    if line:
                        message = line.decode("utf-8", "replace")
                        message = re.sub(r"(?i)\b(pass|password)=\S*", r"\1=<redacted>", message)
                        if config is not None and config.password:
                            message = message.replace(config.password, "<redacted>")
                        replies.append(message[:500])
                    if line.startswith(b"ERR "):
                        raise RuntimeError(replies[-1])
                    if line == b"OK saved":
                        saved = True
                    state = parse_state(line)
                    if saved and state and state.get("ready") == "1":
                        info = state
                        break
                if info is not None:
                    break
                # Poll after CONFIG too: READY can be missed/delayed during AP
                # startup. Keep the OK-saved gate to reject stale startup state;
                # STATUS queries do not restart Wi-Fi or rewrite credentials.
                if time.monotonic() - last_query >= 1:
                    ser.write(b"STATUS\n")
                    last_query = time.monotonic()
            if info is None:
                stage = ("Configuration acknowledged (OK saved), but no ready reply."
                         if provision and saved else
                         "No configuration acknowledgment (OK saved)." if provision else
                         "No ready STATUS reply.")
                recent = "\n".join(replies) if replies else "(no complete serial replies)"
                raise TimeoutError(f"USB setup timed out after {timeout:g}s at {BAUD} baud. {stage}\n"
                                   f"Recent ESP32 replies:\n{recent}")
            if provision:
                expected = "ap" if config.mode.lower() == "esp32" else config.mode.lower()
                if info.get("mode") != expected:
                    raise RuntimeError("Device reported a different mode from the requested configuration.")
            if info.get("format") != "frame8" or info.get("channels") != "8":
                raise RuntimeError("This recorder needs format=frame8. Disable SD playback for the alpha test.")
            if info.get("protocol") not in ("ack1", "ack2"):
                raise RuntimeError("Upload the reliable-stream Main firmware (protocol=ack1 or ack2 required).")
            if info.get("mode") not in ("uart", "ap", "personal", "enterprise"):
                raise RuntimeError("Unknown mode in device handshake.")
            info["port"] = int(info["port"])
            info["baud"] = int(info["baud"])
            info["fs"] = float(info["fs"])
            if info["baud"] != BAUD or not 1 <= info["port"] <= 65535 or not math.isfinite(info["fs"]) or info["fs"] <= 0:
                raise RuntimeError("Invalid transport/sample settings in handshake.")
            if info["mode"] != "uart" and info.get("ip") in (None, "0.0.0.0"):
                raise RuntimeError("Device has no usable network address.")
            if config_file is not None:
                # Save connection metadata only; never store Wi-Fi passwords here.
                Path(config_file).write_text(json.dumps({**info, "com_port": com_port}, indent=2), encoding="utf-8")
            return cls(ser, info)
        except BaseException:
            ser.close()
            raise

    def record(self, seconds=30, output=None, progress=print, recovery_timeout=15):
        from .b2bci_reliable import reliable_record
        if output is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output = Path(f"esp32_all_channels_{stamp}.csv")
        else:
            output = Path(output)
        return reliable_record(self.serial, self.info, output, seconds=seconds,
                               progress=progress, recovery_timeout=recovery_timeout)

    def close(self):
        self.serial.close()
