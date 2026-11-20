"""Checked batches, durable acknowledgments, and reconnect/replay for frame8."""
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import json
import math
import os
import secrets
import socket
import time
import zlib

from .b2bci_client import CSV_COLUMNS, CaptureStats, parse_frame


@dataclass
class ReliableStats(CaptureStats):
    retry_requests: int = 0
    reconnections: int = 0
    sender_retries: int = 0
    late_samples: int = 0
    peak_buffer_frames: int = 0
    source_first_frame: int | None = None
    source_last_frame: int | None = None
    stopped_by_user: bool = False
    complete: bool = False
    buffer_frames: int | None = None
    buffer_capacity: int | None = None
    source_gap_frames: int = 0
    buffer_dropped_frames: int = 0
    invalid_source_packets: int = 0
    unresolved_invalid_packets: int = 0
    source_duplicates: int = 0
    source_timeline_frames: int = 0
    lossless: bool | None = None


@dataclass
class Batch:
    session: str
    first: int
    last: int
    crc: int
    rows: list
    ordinal: int | None = None


class BatchDecoder:
    """Resynchronize at BATCH headers after partial/corrupt serial data."""
    def __init__(self, allow_gaps=False):
        self.allow_gaps = allow_gaps
        self.reset()

    def reset(self):
        self.pending = bytearray()
        self.header = None
        self.payload = bytearray()
        self.discard_line = False

    def feed(self, chunk):
        self.pending.extend(chunk)
        events = []
        while True:
            end = self.pending.find(b"\n")
            if end < 0:
                if len(self.pending) > 8192:
                    self.pending.clear()
                    self.header = None
                    self.payload.clear()
                    self.discard_line = True
                    events.append(("bad", "overlong line"))
                return events
            line = bytes(self.pending[:end + 1])
            del self.pending[:end + 1]
            if self.discard_line:
                self.discard_line = False
                continue
            if line.startswith(b"# BATCH "):
                if self.header:
                    events.append(("bad", "incomplete batch"))
                self.header = None
                self.payload.clear()
                try:
                    parts = line.decode("ascii").split()
                    if len(parts) != (8 if self.allow_gaps else 7):
                        raise ValueError("invalid batch header")
                    _, _, session, first, count, size, crc = parts[:7]
                    first, count, size, crc = int(first), int(count), int(size), int(crc, 16)
                    ordinal = int(parts[7]) if self.allow_gaps else None
                    if ordinal is not None and not 1 <= ordinal <= ordinal + count - 1 <= 0xFFFFFFFF:
                        raise ValueError("invalid delivery ordinal")
                    if len(session) != 16 or not all(c in "0123456789abcdefABCDEF" for c in session):
                        raise ValueError("invalid session")
                    if not (1 <= count <= 16 and 1 <= first <= first + count - 1 <= 0xFFFFFFFF
                            and 1 <= size <= 8192 and 0 <= crc <= 0xFFFFFFFF):
                        raise ValueError("invalid batch dimensions")
                    self.header = session, first, count, size, crc, ordinal
                except (ValueError, UnicodeError) as exc:
                    events.append(("bad", str(exc)))
            elif line.startswith(b"# END "):
                if self.header is None:
                    continue
                session, first, count, size, crc, ordinal = self.header
                payload = bytes(self.payload)
                self.header = None
                self.payload.clear()
                try:
                    parts = line.decode("ascii").split()
                    if len(parts) != 4 or parts[2] != session:
                        raise ValueError("batch end mismatch")
                    last = int(parts[3])
                    if len(payload) != size or zlib.crc32(payload) != crc:
                        raise ValueError("batch checksum/length mismatch")
                    rows = [parse_frame(row) for row in payload.splitlines()]
                    if len(rows) != count or any(row is None for row in rows):
                        raise ValueError("batch sequence mismatch")
                    if rows[0][0] != first or rows[-1][0] != last:
                        raise ValueError("batch endpoint mismatch")
                    if self.allow_gaps:
                        if any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
                            raise ValueError("non-increasing source sequence")
                    elif any(row[0] != first + i for i, row in enumerate(rows)):
                        raise ValueError("batch sequence mismatch")
                    events.append(("batch", Batch(session, first, last, crc, rows, ordinal)))
                except (ValueError, UnicodeError) as exc:
                    events.append(("bad", str(exc)))
            elif self.header is not None:
                self.payload.extend(line)
                if len(self.payload) > 8192:
                    self.header = None
                    self.payload.clear()
                    events.append(("bad", "oversized batch"))
            elif line.startswith((b"# SESSION ", b"# DONE ", b"# ERROR ", b"# HEALTH ")):
                try:
                    events.append(("control", line.decode("ascii").split()))
                except UnicodeError:
                    events.append(("bad", "invalid control line"))


class RecordingLink:
    def __init__(self, serial_handle, info):
        self.serial = serial_handle
        self.info = info
        self.sock = None

    def open(self):
        if self.info["mode"] == "uart":
            if not self.serial.is_open:
                raise OSError("Serial connection is closed; cannot safely resume a reset board.")
        else:
            self.sock = socket.create_connection((self.info["ip"], self.info["port"]), timeout=2)
            self.sock.settimeout(0.2)

    def send(self, command):
        # Terminate any old partial command before sending the next one.
        data = ("\n" + command + "\n").encode("ascii")
        if self.info["mode"] == "uart":
            sent = 0
            while sent < len(data):
                n = self.serial.write(data[sent:])
                if not n:
                    raise OSError("Serial command write stalled.")
                sent += n
        else:
            if self.sock is None:
                raise OSError("TCP connection is not open.")
            self.sock.sendall(data)

    def read(self):
        if self.info["mode"] == "uart":
            return self.serial.read(min(8192, self.serial.in_waiting or 1))
        try:
            data = self.sock.recv(8192)
        except socket.timeout:
            return b""
        if not data:
            raise OSError("TCP connection closed.")
        return data

    def disconnect(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None


def reliable_record(serial_handle, info, output, seconds=30, progress=print,
                    recovery_timeout=15, *, link_factory=RecordingLink, session_id=None):
    if info.get("protocol") not in ("ack1", "ack2"):
        raise RuntimeError("Upload the reliable-stream firmware and rerun setup (protocol=ack1 or ack2 required).")
    gap_mode = info["protocol"] == "ack2"
    if gap_mode:
        from .b2bci_capture_log import CaptureLog, checked_report
    if seconds is not None and (not math.isfinite(seconds) or seconds <= 0):
        raise ValueError("seconds must be positive and finite, or None.")
    if not math.isfinite(recovery_timeout) or recovery_timeout <= 0:
        raise ValueError("recovery_timeout must be positive and finite.")
    limit = 0 if seconds is None else max(1, round(seconds * info["fs"]))
    if limit > 0xFFFFFFFF:
        raise ValueError("Requested recording exceeds the uint32 frame limit.")
    output = Path(output)
    sidecar = output.with_suffix(output.suffix + ".json")
    if sidecar.exists():
        raise FileExistsError(sidecar)
    session = session_id or secrets.token_hex(8)
    if len(session) != 16 or any(c not in "0123456789abcdefABCDEF" for c in session):
        raise ValueError("Recording session ID must be 16 hexadecimal characters.")
    stats = ReliableStats()
    decoder = BatchDecoder(allow_gaps=gap_mode)
    capture_log = CaptureLog(output) if gap_mode else None
    previous_timestamp = None
    link = link_factory(serial_handle, info)
    started = connected = stopping = created = False
    have_connected = False
    expected = 1
    start = last_progress = last_report = last_command = time.monotonic()
    failure = None
    metadata = {"session": session, "protocol": info["protocol"], "mode": info["mode"],
                "source": info.get("source", "unknown"),
                "requested_frames": limit, "sample_rate": info["fs"], "complete": False}
    if capture_log:
        metadata.update(gaps_file=capture_log.gaps_path.name, buffer_history_file=capture_log.buffer_path.name,
                        frame_numbering="source timeline relative to first valid frame; gaps preserved",
                        completion_means="all retained samples saved; inspect lossless and loss counts")

    def request_retry():
        stats.retry_requests += 1
        link.send(f"RETRY {session}")

    try:
        with output.open("x", newline="", encoding="utf-8") as handle:
            created = True
            writer = csv.writer(handle)
            writer.writerow(CSV_COLUMNS)
            sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            if capture_log:
                capture_log.open()
            while not stats.complete:
                now = time.monotonic()
                if now - last_progress > recovery_timeout:
                    raise TimeoutError("No recording progress within recovery timeout. Partial CSV retained; "
                                       "the ESP32 may be disconnected, reset, or its replay buffer may be full.")
                try:
                    if not connected:
                        link.open()
                        decoder.reset()
                        link.send(f"RESUME {session}" if started else f"BEGIN {session} {limit}")
                        if stopping:
                            link.send(f"STOP {session}")
                        connected = True
                        if have_connected:
                            stats.reconnections += 1
                        have_connected = True
                        last_command = now
                    events = decoder.feed(link.read())
                    for kind, event in events:
                        if kind == "bad":
                            stats.bad_lines += 1
                            request_retry()
                        elif kind == "control":
                            if len(event) < 4 or event[2] != session:
                                continue
                            if event[1] == "ERROR":
                                raise RuntimeError("ESP32 recording failed: " + " ".join(event[3:]))
                            if gap_mode and event[1] in ("HEALTH", "DONE"):
                                if not started:
                                    continue
                                try:
                                    values = checked_report(event)
                                    if limit and values["produced"] > limit:
                                        raise ValueError("Source timeline exceeds requested limit")
                                    if event[1] == "DONE":
                                        if (values["saved"] != stats.samples or values["queued"] != 0
                                                or values["ack"] != (stats.last_frame or 0)
                                                or values["produced"] < (stats.last_frame or 0)
                                                or (limit and not stopping and values["produced"] != limit)):
                                            raise ValueError("Completion does not match saved rows")
                                    capture_log.report(values, stats)
                                    if info.get("source") != "stm32" or not values["produced"]:
                                        stats.source_first_frame = stats.source_last_frame = None
                                except (ValueError, UnicodeError):
                                    stats.bad_lines += 1
                                    request_retry()
                                    continue
                                # A checked heartbeat shows the session is alive even while
                                # a full ring discards new arrivals or the source is paused.
                                last_progress = time.monotonic()
                                if event[1] == "DONE":
                                    capture_log.gap(expected, values["produced"], stats.last_frame, None,
                                                    previous_timestamp, None)
                                    capture_log.sync()
                                    stats.dropped_frames = values["produced"] - stats.samples
                                    stats.lossless = stats.dropped_frames == 0 and values["invalid"] == 0
                                    stats.complete = True
                                continue
                            if event[1] == "SESSION":
                                try:
                                    valid = len(event) == 5 and int(event[3]) == limit and event[4] == info["protocol"]
                                except ValueError:
                                    valid = False
                                if not valid:
                                    raise RuntimeError("Recording session parameters do not match the request.")
                                started = True
                                if stopping:
                                    link.send(f"STOP {session}")
                            elif event[1] == "DONE":
                                try:
                                    last = int(event[3])
                                except ValueError:
                                    request_retry()
                                    continue
                                if not started or last != expected - 1 or (limit and not stopping and last != limit):
                                    request_retry()
                                    continue
                                values = dict(part.split("=", 1) for part in event[4:] if "=" in part)
                                try:
                                    metrics = [int(values.get(k, 0)) for k in ("retries", "late", "peak")]
                                    if any(v < 0 for v in metrics):
                                        raise ValueError("negative metric")
                                    source_first = int(values["source_first"]) if "source_first" in values else None
                                    source_last = int(values["source_last"]) if "source_last" in values else None
                                    if info.get("source") == "stm32" and (source_first is None or source_last is None):
                                        raise ValueError("STM32 completion is missing original counters")
                                    if (source_first is None) != (source_last is None):
                                        raise ValueError("Incomplete source counter pair")
                                    if source_first is not None:
                                        if not (0 <= source_first <= 0xFFFFFFFF and 0 <= source_last <= 0xFFFFFFFF):
                                            raise ValueError("Invalid source counters")
                                        if last and ((source_first + last - 1) & 0xFFFFFFFF) != source_last:
                                            raise ValueError("STM32 source counter span differs from saved count")
                                except ValueError:
                                    request_retry()
                                    continue
                                stats.sender_retries, stats.late_samples, stats.peak_buffer_frames = metrics
                                stats.source_first_frame, stats.source_last_frame = source_first, source_last
                                stats.complete = True
                        elif kind == "batch":
                            batch = event
                            if batch.session != session:
                                continue
                            if not started:
                                link.send(f"BEGIN {session} {limit}")
                                continue
                            if not gap_mode and batch.first > expected:
                                request_retry() # Do not write past a missing frame.
                                continue
                            if limit and batch.last > limit:
                                raise RuntimeError("ESP32 sent frames beyond the requested recording limit.")
                            if gap_mode:
                                # Delivery ordinals must remain contiguous, even when source
                                # frame numbers have gaps. Missing a transport batch is never
                                # accepted as a source loss.
                                if batch.ordinal > stats.samples + 1:
                                    request_retry()
                                    continue
                                overlap = min(len(batch.rows), max(0, stats.samples + 1 - batch.ordinal))
                                new_rows = batch.rows[overlap:]
                                if ((overlap and batch.rows[overlap - 1][0] > (stats.last_frame or 0))
                                        or (new_rows and new_rows[0][0] < expected)):
                                    request_retry()
                                    continue
                            else:
                                new_rows = [row for row in batch.rows if row[0] >= expected]
                            stats.duplicates += len(batch.rows) - len(new_rows)
                            for row in new_rows:
                                if not gap_mode and row[0] != expected:
                                    raise RuntimeError("Noncontiguous frame in verified batch.")
                                if capture_log:
                                    capture_log.gap(expected, row[0] - 1, stats.last_frame, row[0],
                                                    previous_timestamp, row[1])
                                writer.writerow(row)
                                if gap_mode:
                                    stats.samples += 1
                                    stats.last_frame = row[0]
                                    stats.dropped_frames = max(stats.dropped_frames, row[0] - stats.samples)
                                else:
                                    stats.accept(row[0])
                                previous_timestamp = row[1]
                                expected = row[0] + 1
                            # ACK means committed to the CSV, not merely read from a socket.
                            # If this fails, no ACK is sent and the device retains the batch.
                            if new_rows:
                                handle.flush()
                                os.fsync(handle.fileno())
                                if capture_log:
                                    capture_log.sync()
                                last_progress = time.monotonic()
                            link.send(f"ACK {session} {batch.last} {batch.crc:08x}")
                    if not started and time.monotonic() - last_command >= 1:
                        link.send(f"BEGIN {session} {limit}")
                        last_command = time.monotonic()
                    elif stopping and time.monotonic() - last_command >= 1:
                        link.send(f"STOP {session}")
                        last_command = time.monotonic()
                except LinkError:
                    connected = False
                    link.disconnect()
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    if stopping:
                        raise
                    stopping = True
                    stats.stopped_by_user = True
                    if progress:
                        progress("Stopping acquisition and saving the retained tail; interrupt again to abort.")
                    try:
                        link.send(f"STOP {session}")
                    except (OSError, LinkError):
                        connected = False
                        link.disconnect()
                now = time.monotonic()
                if progress and now - last_report >= 1:
                    buffer_status = (f" | buffer={stats.buffer_frames}/{stats.buffer_capacity} "
                                     f"({100 * stats.buffer_frames / stats.buffer_capacity:.0f}%)"
                                     f" | peak={stats.peak_buffer_frames} | source_gaps={stats.source_gap_frames}"
                                     f" | buffer_drops={stats.buffer_dropped_frames}"
                                     f" | invalid_source={stats.invalid_source_packets}"
                                     if stats.buffer_capacity else "")
                    progress(f"samples={stats.samples} | received={stats.samples / max(now-start, 0.001):.1f} Hz | "
                             f"dropped={stats.dropped_frames} | retries={stats.retry_requests} | "
                             f"duplicates={stats.duplicates} | reconnects={stats.reconnections} | bad_blocks={stats.bad_lines}"
                             + buffer_status)
                    last_report = now
    except BaseException as exc:
        stats.complete = False
        failure = f"{type(exc).__name__}: {exc}"
        if progress and created:
            progress(f"Recording incomplete; partial CSV preserved at {output.resolve()}")
        raise
    finally:
        if connected and stats.complete:
            try:
                link.send(f"CANCEL {session}")
            except (OSError, LinkError):
                pass
        link.disconnect()
        log_error = None
        if capture_log:
            try:
                capture_log.close()
            except OSError as exc:
                stats.complete = False
                if failure is None:
                    failure = f"{type(exc).__name__}: {exc}"
                    log_error = exc
        if created:
            metadata.update(complete=stats.complete, error=failure, stats=asdict(stats))
            try:
                sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            except OSError:
                if failure is None:
                    raise
        if log_error is not None:
            raise log_error
    if progress:
        if gap_mode:
            progress(f"Saved {stats.samples} samples | missing={stats.dropped_frames} | "
                     f"invalid_source={stats.invalid_source_packets} | peak={stats.peak_buffer_frames}/{stats.buffer_capacity} "
                     f"| complete={stats.complete} | lossless={stats.lossless} | {output.resolve()}")
        else:
            progress(f"Saved {stats.samples} contiguous samples to {output.resolve()}")
    return output, stats


class LinkError(Exception):
    """A retryable transport error, distinct from disk/CSV failures."""


# Translate only transport OSErrors. A disk error must never trigger replay into
# a partially written CSV as if it were a connection interruption.
def _transport_errors(method):
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except OSError as exc:
            raise LinkError(str(exc)) from exc
    return wrapped


RecordingLink.open = _transport_errors(RecordingLink.open)
RecordingLink.send = _transport_errors(RecordingLink.send)
RecordingLink.read = _transport_errors(RecordingLink.read)
