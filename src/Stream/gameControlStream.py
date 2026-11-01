"""Temporary input adapters. No controller owns a game or UI reference."""

from threading import Lock

import numpy as np
import scipy.io as sio

from Classes.controllerState import ControllerState
from Classes.featureClass import FeatureClass, FeatureType
from Stream.dataStream import DataStream, StreamType
from common import ALPHA, QUEUE_LENGTH, SAMPLING_FREQ


ALPHA_WINDOW = 100


def source_chain(source):
    """Follow stream dependencies, rejecting accidental reference cycles."""
    seen = set()
    while source is not None:
        if id(source) in seen:
            raise ValueError("The selected source has a circular dependency")
        seen.add(id(source))
        yield source
        source = getattr(source, "reference_stream", None)


def stopped_sources(source):
    return [stream.stream_name for stream in source_chain(source)
            if not stream.is_alive() or stream.shutdown_event.is_set()]


def sampling_frequency(source):
    for stream in source_chain(source):
        for name in ("fs", "sampling_frequency", "sampling_rate", "sample_rate"):
            value = getattr(stream, name, None)
            if value is not None:
                value = float(value)
                if not np.isfinite(value) or value <= 0:
                    raise ValueError("Source sampling frequency must be positive")
                return value
    return SAMPLING_FREQ


def latest_label(source):
    samples = source.data.copy()
    if not samples:
        return None
    value = np.asarray(samples[-1])
    if value.size != 1:
        raise ValueError("Control input must contain one label per sample")
    scalar = value.item()
    if not isinstance(scalar, (str, bool, int, float)):
        raise ValueError("Control input must be a text or numeric label")
    if isinstance(scalar, (int, float)) and not np.isfinite(scalar):
        raise ValueError("Control label must be finite")
    return str(scalar)


def channel_count(source):
    """Inspect sample-major data without the base stream's shape heuristic."""
    samples = source.data.copy()
    if not samples:
        return source.get_num_channels()
    sample = np.asarray(samples[-1])
    if sample.ndim == 0:
        return 1
    if sample.ndim == 1 and sample.size:
        return sample.size
    raise ValueError("Alpha input must contain scalar or channel-vector samples")


class GameControlStream(DataStream):
    def __init__(self, reference_stream: DataStream, *, mode="label",
                 active_label="eyesOpen", channel_index=0, threshold=None,
                 invert=False, stream_name="GameControl"):
        super().__init__(stream_name, StreamType.CONTROL, queue_length=1)
        if mode not in ("label", "alpha"):
            raise ValueError("Controller mode must be label or alpha")
        if channel_index < 0:
            raise ValueError("Choose a valid channel")
        self.reference_stream = reference_stream
        self.mode = mode
        self.active_label = str(active_label)
        self.channel_index = channel_index
        self.invert = invert
        self._lock = Lock()
        self._threshold = None
        self._invalid_reason = None
        self._state = ControllerState()
        self._alpha_feature = FeatureClass(FeatureType.ALPHA)
        if threshold is not None:
            self.set_threshold(threshold)

    def read_state(self) -> ControllerState:
        with self._lock:
            return self._state

    def set_threshold(self, value) -> None:
        try:
            threshold = float(value)
        except (ValueError, TypeError):
            raise ValueError("Threshold must be a finite, nonnegative number")
        if not np.isfinite(threshold) or threshold < 0:
            raise ValueError("Threshold must be a finite, nonnegative number")
        with self._lock:
            self._threshold = threshold
            if self._state.ready and self._state.power is not None:
                self._state = self._alpha_state(self._state.power)

    def invalidate(self, reason: str) -> None:
        """Permanently detach a removed/replaced inventory source."""
        with self._lock:
            self._invalid_reason = reason
            self._state = ControllerState(
                status="unavailable", message=reason,
                threshold=self._threshold)

    def _alpha_state(self, power):
        if self._threshold is None:
            self._threshold = power
        above = power > self._threshold
        return ControllerState(
            upper_lane=not above if self.invert else above,
            status="ready", message="Alpha input ready", power=power,
            threshold=self._threshold)

    def _evaluate(self):
        stopped = stopped_sources(self.reference_stream)
        if stopped:
            return ControllerState(
                status="unavailable",
                message="Start in Inventory: " + ", ".join(stopped))
        if self.mode == "label":
            label = latest_label(self.reference_stream)
            if label is None:
                return ControllerState(message="Waiting for a control label")
            return ControllerState(
                upper_lane=label == self.active_label, status="ready",
                message="Control input ready", label=label)

        capacity = self.reference_stream.data.maxlen
        if capacity is not None and capacity < ALPHA_WINDOW:
            raise ValueError("Alpha input needs a buffer of at least 100 samples")
        samples = list(self.reference_stream.data.copy())[-ALPHA_WINDOW:]
        if len(samples) < ALPHA_WINDOW:
            return ControllerState(
                message=f"Waiting for alpha samples ({len(samples)}/{ALPHA_WINDOW})")
        data = np.asarray(samples, dtype=float)
        if data.ndim == 1:
            data = data[:, np.newaxis]
        if data.ndim != 2:
            raise ValueError("Alpha input must have samples × channels shape")
        if self.channel_index >= data.shape[1]:
            raise ValueError("The selected channel is unavailable")
        channel = data[:, self.channel_index]
        if not np.all(np.isfinite(channel)):
            raise ValueError("Alpha input contains nonfinite samples")
        fs = sampling_frequency(self.reference_stream)
        frequencies = np.fft.rfftfreq(ALPHA_WINDOW, 1 / fs)
        if not np.any((frequencies >= ALPHA[0]) & (frequencies <= ALPHA[1])):
            raise ValueError("This sampling frequency has no alpha bins in 100 samples")
        with np.errstate(over="ignore", invalid="ignore"):
            power = float(self._alpha_feature.apply(channel, fs))
        if not np.isfinite(power):
            raise ValueError("Alpha power is not finite")
        with self._lock:
            return self._alpha_state(power)

    def update_once(self) -> ControllerState:
        """Evaluate a copied source buffer and publish one atomic snapshot."""
        try:
            state = self._evaluate()
        except Exception as error:
            state = ControllerState(status="invalid", message=str(error))
        with self._lock:
            if self._invalid_reason:
                state = ControllerState(
                    status="unavailable", message=self._invalid_reason,
                    threshold=self._threshold)
            elif self.mode == "alpha":
                # Recompute the decision if a threshold edit raced evaluation.
                if state.ready:
                    state = self._alpha_state(state.power)
                else:
                    state = ControllerState(
                        status=state.status, message=state.message,
                        threshold=self._threshold)
            self._state = state
            self.data.append(state.upper_lane if state.ready else False)
            return state

    def _stream(self):
        interval = 0.1 if self.mode == "alpha" else 1 / 60
        while not self.shutdown_event.is_set():
            self.update_once()
            self.shutdown_event.wait(interval)

    def stop(self):
        super().stop()
        with self._lock:
            self._state = ControllerState(
                status="unavailable", message="Controller stopped",
                threshold=self._threshold)


class MatFileStream(DataStream):
    def __init__(self, mat_path, stream_name="EEG_Mat",
                 stream_type=StreamType.SOFTWARE, queue_length=QUEUE_LENGTH):
        mat = sio.loadmat(mat_path)
        eyes_open = mat['eyesOpen']
        eyes_closed = mat['eyesClosed']
        self.samples = []
        for i in range(eyes_open.shape[0]):
            self.samples.extend(eyes_open[i])
            self.samples.extend(eyes_closed[i])
        self.sample_index = 0
        super().__init__(stream_name, stream_type, queue_length)

    def _stream(self):
        while not self.shutdown_event.is_set():
            self.data.append(np.array([self.samples[self.sample_index]]))
            self.sample_index = (self.sample_index + 1) % len(self.samples)
            self.shutdown_event.wait(1 / SAMPLING_FREQ)
