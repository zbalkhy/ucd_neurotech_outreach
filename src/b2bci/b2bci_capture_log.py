"""Durable gap records and sampled ring-buffer history for ack2 recordings."""
import csv
import json
import os
from pathlib import Path
import time
import zlib


def checked_report(event):
    """Verify report CRC before trusting source-loss or occupancy counters."""
    if len(event) < 6 or event[1] not in ("HEALTH", "DONE") or not event[-1].startswith("crc="):
        raise ValueError("Missing capture report checksum")
    body = " ".join(event[1:-1]).encode("ascii")
    if zlib.crc32(body) != int(event[-1][4:], 16):
        raise ValueError("Capture report checksum mismatch")
    pairs = [part.split("=", 1) for part in event[4:-1]]
    values = {k: int(v) for k, v in pairs}
    required = {"saved", "ack", "queued", "capacity", "peak", "source_gaps", "overflow_drops",
                "invalid", "unresolved", "source_duplicates", "source_first", "source_last", "late", "retries"}
    if set(values) != required or len(pairs) != len(required):
        raise ValueError("Incomplete capture report")
    values["produced"] = int(event[3])
    if any(not 0 <= v <= 0xFFFFFFFF for v in values.values()):
        raise ValueError("Invalid capture counter")
    if not (0 <= values["queued"] <= values["peak"] <= values["capacity"] and values["capacity"] > 0):
        raise ValueError("Invalid buffer occupancy")
    if values["saved"] + values["source_gaps"] + values["overflow_drops"] != values["produced"]:
        raise ValueError("Source timeline accounting mismatch")
    if values["queued"] > values["saved"] or values["ack"] > values["produced"]:
        raise ValueError("Invalid acknowledgment accounting")
    if values["unresolved"] > values["invalid"]:
        raise ValueError("Invalid unresolved packet count")
    return values


class CaptureLog:
    def __init__(self, output):
        self.gaps_path = Path(str(output) + ".gaps.jsonl")
        self.buffer_path = Path(str(output) + ".buffer.csv")
        self.gaps = self.history = None
        self.dirty = False
        self.start = time.monotonic()
        self.last_report = None

    def open(self):
        self.gaps = self.gaps_path.open("x", encoding="utf-8")
        self.history = self.buffer_path.open("x", newline="", encoding="utf-8")
        self.writer = csv.writer(self.history)
        self.writer.writerow(["host_seconds", "source_frames", "retained_total", "ack_frame", "buffer_frames",
                              "capacity", "fill_percent", "peak_frames", "source_gaps", "buffer_drops",
                              "invalid_packets", "unresolved_invalid", "sender_retries"])
        self.history.flush()

    def gap(self, first, last, previous_frame, next_frame, previous_ms, next_ms):
        if first > last:
            return
        self.gaps.write(json.dumps({"type": "missing_samples", "first_frame": first, "last_frame": last,
                                   "count": last - first + 1, "previous_saved_frame": previous_frame,
                                   "next_saved_frame": next_frame, "previous_time_ms": previous_ms,
                                   "next_time_ms": next_ms}) + "\n")
        self.dirty = True

    def sync(self):
        if self.dirty:
            self.gaps.flush()
            os.fsync(self.gaps.fileno())
            self.dirty = False

    def report(self, values, stats):
        if self.last_report is not None:
            monotonic = ("produced", "saved", "ack", "peak", "source_gaps", "overflow_drops",
                         "invalid", "source_duplicates", "late", "retries")
            if any(values[k] < self.last_report[k] for k in monotonic):
                raise ValueError("Capture counters moved backwards")
            if values["capacity"] != self.last_report["capacity"]:
                raise ValueError("Buffer capacity changed")
        self.last_report = values
        stats.buffer_frames, stats.buffer_capacity = values["queued"], values["capacity"]
        stats.peak_buffer_frames = values["peak"]
        stats.source_gap_frames, stats.buffer_dropped_frames = values["source_gaps"], values["overflow_drops"]
        stats.invalid_source_packets, stats.unresolved_invalid_packets = values["invalid"], values["unresolved"]
        stats.source_duplicates = values["source_duplicates"]
        stats.source_timeline_frames = values["produced"]
        stats.sender_retries, stats.late_samples = values["retries"], values["late"]
        stats.dropped_frames = max(stats.dropped_frames, values["source_gaps"] + values["overflow_drops"])
        stats.source_first_frame, stats.source_last_frame = values["source_first"], values["source_last"]
        self.writer.writerow([round(time.monotonic() - self.start, 3), values["produced"], values["saved"],
                              values["ack"], values["queued"], values["capacity"],
                              round(100 * values["queued"] / values["capacity"], 2), values["peak"],
                              values["source_gaps"], values["overflow_drops"], values["invalid"],
                              values["unresolved"], values["retries"]])
        self.history.flush()

    def close(self):
        try:
            self.sync()
        finally:
            if self.gaps is not None:
                self.gaps.close()
            if self.history is not None:
                self.history.close()
