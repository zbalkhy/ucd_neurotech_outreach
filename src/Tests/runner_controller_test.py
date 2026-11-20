from dataclasses import FrozenInstanceError
from threading import Thread
from time import monotonic, sleep

import numpy as np
import pytest

from Classes.controllerState import ControllerState
from Classes.featureClass import FeatureClass, FeatureType
from Game.week1_game import InfiniteRunner
from Models.userModel import UserModel
from Stream.dataStream import DataStream, StreamType
from Stream.gameControlStream import (
    GameControlStream, channel_count, sampling_frequency,
)
from ViewModel.runnerViewModel import RunnerViewModel


class HoldingStream(DataStream):
    """A live producer whose samples are explicitly supplied by each test."""

    def _stream(self):
        self.shutdown_event.wait()


@pytest.fixture
def sources():
    streams = []

    def create(name="source", kind=StreamType.SOFTWARE, capacity=250):
        stream = HoldingStream(name, kind, capacity)
        stream.start()
        streams.append(stream)
        return stream

    yield create
    for stream in reversed(streams):
        stream.stop()


def fill_signal(source, frequency=10, amplitude=1, channels=False):
    time = np.arange(100) / 250
    signal = amplitude * np.sin(2 * np.pi * frequency * time)
    source.data.clear()
    if channels:
        source.data.extend(np.column_stack([np.zeros(100), signal]))
    else:
        source.data.extend(signal)
    return signal


@pytest.mark.parametrize("sample,label,upper", [
    ("eyesOpen", "eyesOpen", True),
    ("eyesClosed", "eyesOpen", False),
    (np.array(["custom"]), "custom", True),
    (np.array([["custom"]]), "custom", True),
    (np.array([1]), "1", True),
    (True, "True", True),
])
def test_label_mapping_uses_latest_sample(sources, sample, label, upper):
    source = sources(kind=StreamType.CONTROL)
    source.data.extend(["old", sample])
    controller = GameControlStream(source, active_label=label)
    state = controller.update_once()
    assert state.ready and state.upper_lane == upper
    assert not hasattr(controller, "game")
    with pytest.raises(FrozenInstanceError):
        state.upper_lane = False


@pytest.mark.parametrize("sample", [np.array([1, 2]), None, np.nan, np.inf])
def test_invalid_labels_pause(sources, sample):
    source = sources(kind=StreamType.CONTROL)
    source.data.append(sample)
    state = GameControlStream(source).update_once()
    assert state.status == "invalid"
    assert not state.ready


def test_empty_label_and_stopped_upstream_recover(sources):
    source = sources(kind=StreamType.CONTROL)
    upstream = sources(name="upstream")
    source.reference_stream = upstream
    controller = GameControlStream(source)
    assert controller.update_once().status == "waiting"
    source.data.append("eyesOpen")
    upstream.stop()
    state = controller.update_once()
    assert not state.ready and "upstream" in state.message
    upstream.start()
    assert controller.update_once().upper_lane


def test_alpha_matches_feature_and_uses_only_selected_channel(sources):
    source = sources()
    signal = fill_signal(source, channels=True)
    expected = float(FeatureClass(FeatureType.ALPHA).apply(signal, 250))
    controller = GameControlStream(source, mode="alpha", channel_index=1)
    state = controller.update_once()
    assert state.power == expected
    assert state.threshold == expected
    assert not state.upper_lane  # Equality is the lower lane.
    assert GameControlStream(source, mode="alpha").update_once().power == 0
    assert channel_count(source) == 2
    controller.set_threshold(expected / 2)
    assert controller.read_state().upper_lane
    fill_signal(source, amplitude=2, channels=True)
    state = controller.update_once()
    assert state.power == pytest.approx(4 * expected)
    assert state.threshold == expected / 2  # No automatic recalibration.


def test_alpha_uses_latest_100_samples(sources):
    source = sources()
    signal = fill_signal(source)
    source.data.clear()
    source.data.extend(np.full(150, 1000000))
    source.data.extend(signal)
    state = GameControlStream(source, mode="alpha").update_once()
    assert state.power == float(FeatureClass(FeatureType.ALPHA).apply(signal, 250))


def test_out_of_band_and_inversion(sources):
    source = sources()
    fill_signal(source, frequency=30)
    normal = GameControlStream(source, mode="alpha", threshold=1)
    inverse = GameControlStream(source, mode="alpha", threshold=1, invert=True)
    assert normal.update_once().power < 1e-20
    assert not normal.read_state().upper_lane
    assert inverse.update_once().upper_lane
    fill_signal(source)
    assert normal.update_once().upper_lane
    assert not inverse.update_once().upper_lane
    inverse.set_threshold(inverse.read_state().power)
    assert inverse.read_state().upper_lane


@pytest.mark.parametrize("bad", ["", "bad", "nan", "inf", "-inf", -1, None])
def test_threshold_validation_retains_last_value(sources, bad):
    source = sources()
    fill_signal(source)
    controller = GameControlStream(source, mode="alpha", threshold=20)
    controller.update_once()
    with pytest.raises(ValueError):
        controller.set_threshold(bad)
    assert controller.read_state().threshold == 20
    controller.set_threshold("0")
    assert controller.read_state().threshold == 0


def test_alpha_short_buffer_and_channel_shape_errors(sources):
    small = sources(capacity=99)
    assert GameControlStream(small, mode="alpha").update_once().status == "invalid"
    source = sources()
    source.data.extend(range(99))
    controller = GameControlStream(source, mode="alpha")
    assert controller.update_once().status == "waiting"
    source.data.append(99)
    assert controller.update_once().ready
    missing = GameControlStream(source, mode="alpha", channel_index=1)
    assert missing.update_once().status == "invalid"
    source.data.clear()
    source.data.extend(np.ones((100, 1, 1)))
    assert controller.update_once().status == "invalid"


@pytest.mark.parametrize("bad", [np.nan, np.inf, "text"])
def test_alpha_invalid_samples_and_recovery(sources, bad):
    source = sources()
    fill_signal(source)
    source.data.append(bad)
    controller = GameControlStream(source, mode="alpha")
    assert controller.update_once().status == "invalid"
    fill_signal(source)
    assert controller.update_once().ready


def test_sampling_frequency_inheritance_and_invalid_bins(sources):
    source = sources()
    upstream = sources(name="upstream")
    source.reference_stream = upstream
    assert sampling_frequency(source) == 250
    upstream.fs = 500
    assert sampling_frequency(source) == 500
    source.fs = 250
    assert sampling_frequency(source) == 250
    fill_signal(source)
    source.fs = 10000
    assert "no alpha bins" in GameControlStream(source, mode="alpha").update_once().message
    source.fs = -1
    assert GameControlStream(source, mode="alpha").update_once().status == "invalid"
    del source.fs
    upstream.reference_stream = source
    assert GameControlStream(source).update_once().status == "invalid"


def test_controller_thread_stops_without_stopping_source(sources):
    source = sources(kind=StreamType.CONTROL)
    source.data.append("eyesOpen")
    controller = GameControlStream(source)
    try:
        controller.start()
        deadline = monotonic() + 1
        while not controller.read_state().ready and monotonic() < deadline:
            sleep(0.001)
        assert controller.read_state().upper_lane
        assert controller.is_alive()
    finally:
        controller.stop()
    controller.stop()
    assert not controller.is_alive()
    assert not controller.read_state().ready
    assert source.is_alive()


def test_threshold_edits_and_sampling_share_consistent_snapshots(sources):
    source = sources()
    fill_signal(source)
    controller = GameControlStream(source, mode="alpha", threshold=0)
    controller.update_once()

    def edit():
        for i in range(200):
            controller.set_threshold(i)

    thread = Thread(target=edit)
    thread.start()
    for _ in range(200):
        state = controller.update_once()
        assert state.upper_lane == (state.power > state.threshold)
    thread.join()


def test_dead_stream_thread_is_not_alive():
    source = DataStream("empty", StreamType.SOFTWARE)
    source.start()
    source.join()
    first_thread = source._stream_thread
    assert source._stream_thread.ident is not None
    assert not source.is_alive()
    source.start()
    source.join()
    assert source._stream_thread is not first_thread
    assert not source.is_alive()
    source.stop()


class FakeGame:
    def __init__(self, **kwargs):
        self.reader = kwargs['read_controller']
        self.stopped = False
        self.restarts = 0

    def start(self):
        pass

    def stop(self):
        self.stopped = True

    def request_restart(self):
        self.restarts += 1


def test_setup_filters_and_launch_validation(sources):
    user = UserModel()
    streams = [sources(name=kind.name, kind=kind) for kind in StreamType]
    for source in streams:
        user.add_stream(source)
    vm = RunnerViewModel(user, game_factory=FakeGame)
    try:
        assert vm.available_sources() == []
        vm.select_mode("label")
        assert [s.stream_type for s in vm.available_sources()] == [StreamType.CONTROL]
        assert "Choose" in vm.setup_status()
        control = vm.available_sources()[0]
        vm.select_source(control)
        control.stop()
        assert "Start in Inventory" in vm.setup_status()
        with pytest.raises(ValueError):
            vm.start_run()
        assert not control.is_alive()  # Launch never starts shared inputs.
        vm.select_mode("alpha")
        assert {s.stream_type for s in vm.available_sources()} == {
            StreamType.DEVICE, StreamType.FILTER, StreamType.SOFTWARE}
        vm.select_source(vm.available_sources()[0])
        user.remove_stream_by_name(vm.source.stream_name)
        with pytest.raises(ValueError):
            vm.start_run()
    finally:
        vm.dispose()


def test_run_restart_removal_and_cleanup(sources):
    source = sources()
    fill_signal(source)
    user = UserModel()
    user.add_stream(source)
    vm = RunnerViewModel(user, game_factory=FakeGame)
    vm.select_mode("alpha")
    vm.select_source(source)
    try:
        vm.start_run()
        controller = vm.controller
        controller.update_once()
        controller.set_threshold(123)
        vm.restart()
        assert vm.game.restarts == 1
        assert vm.controller is controller
        assert controller.read_state().threshold == 123
        assert user.get_streams() == [source]
        game = vm.game
        user.rename_stream("source", "renamed")
        assert controller.update_once().ready
        replacement = sources(name="renamed")
        user.add_stream(replacement)
        assert "removed or replaced" in controller.read_state().message
        assert not controller.update_once().ready
        vm.stop_run()
        assert game.stopped and not controller.is_alive()
        assert replacement.is_alive()
        vm.select_source(replacement)
        fill_signal(replacement)
        vm.start_run()
        assert vm.controller is not controller
        assert vm.controller.update_once().threshold != 123
    finally:
        vm.dispose()
    vm.dispose()
    assert vm not in user.observers


def test_upstream_removal_invalidates_run(sources):
    source = sources(name="filtered", kind=StreamType.FILTER)
    upstream = sources(name="device", kind=StreamType.DEVICE)
    source.reference_stream = upstream
    fill_signal(source)
    user = UserModel()
    user.add_stream(source)
    user.add_stream(upstream)
    vm = RunnerViewModel(user, game_factory=FakeGame)
    vm.select_mode("alpha")
    vm.select_source(source)
    try:
        vm.start_run()
        user.remove_stream_by_name("device")
        upstream.start()
        assert not vm.controller.update_once().ready
    finally:
        vm.dispose()


def test_keyboard_and_stream_modes_do_not_compete(sources):
    user = UserModel()
    vm = RunnerViewModel(user, game_factory=FakeGame)
    try:
        vm.start_run()
        vm.set_keyboard(True)
        assert vm.controller.read_state().upper_lane
        vm.set_keyboard(False)
        assert not vm.controller.read_state().upper_lane
        vm.stop_run()
        source = sources(kind=StreamType.CONTROL)
        source.data.append("eyesClosed")
        user.add_stream(source)
        vm.select_mode("label")
        vm.select_source(source)
        vm.start_run()
        vm.controller.update_once()
        vm.set_keyboard(True)
        assert not vm.controller.read_state().upper_lane
    finally:
        vm.dispose()


def test_engine_pauses_position_score_and_spawn_clock_then_resumes():
    state = ControllerState(status="ready", upper_lane=True)
    game = InfiniteRunner((800, 600), 60, read_controller=lambda: state)
    game.player = game.Player(game)
    game.step(100)
    position = game.player.rect.y
    state = ControllerState(message="Source stopped")
    game.step(100000)
    assert game.paused
    assert game.player.rect.y == position
    assert game.score == 0 and not game.obstacles
    assert game.active_time_ms == 100
    state = ControllerState(status="ready", upper_lane=True)
    game.step(100000)
    assert not game.paused and not game.obstacles
    assert game.active_time_ms == 100
    game.step(7100)
    assert len(game.obstacles) == 1
    game.score = 5
    game.request_restart()
    game.step(0)
    assert game.score == 0 and not game.obstacles
    assert game.active_time_ms == 0


def test_game_loop_produces_frame_and_joins():
    game = InfiniteRunner((320, 240), 60)
    try:
        game.start()
        deadline = monotonic() + 2
        while game.read_frame() is None and monotonic() < deadline:
            sleep(0.01)
        assert game.error is None
        assert len(game.read_frame()) == 320 * 240 * 3
    finally:
        game.stop()
    game.stop()
    assert not game.thread.is_alive()
