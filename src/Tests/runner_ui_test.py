"""Tk integration checks; requires a display (xvfb on headless Linux)."""

import tkinter as tk
from types import SimpleNamespace

import numpy as np
import pytest

from Models.userModel import UserModel
from Stream.dataStream import DataStream, StreamType
from View.runnerView import RunnerView
from ViewModel.runnerViewModel import RunnerViewModel


class HoldingStream(DataStream):
    def _stream(self):
        self.shutdown_event.wait()


def pump(root, seconds=0.15):
    root.after(int(seconds * 1000), root.quit)
    root.mainloop()


@pytest.fixture
def window():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk requires a display")
    errors = []
    root.report_callback_exception = lambda *error: errors.append(error)
    user = UserModel()
    source = HoldingStream("EEG", StreamType.SOFTWARE, 250)
    signal = np.sin(2 * np.pi * 10 * np.arange(100) / 250)
    source.data.extend(np.column_stack([np.zeros(100), signal]))
    source.start()
    user.add_stream(source)
    control = HoldingStream("Classifier", StreamType.CONTROL, 1)
    control.data.append("eyesOpen")
    control.start()
    user.add_stream(control)
    vm = RunnerViewModel(user)
    view = RunnerView(root, vm)
    yield root, user, source, control, vm, view
    view.on_close()
    source.stop()
    control.stop()
    assert not errors


def choose(view, mode, index=0):
    view.mode.set(mode)
    view._change_mode()
    view.source_combo.current(index)
    view._change_source()


def test_setup_refresh_keyboard_focus_and_repeated_runs(window):
    root, user, source, control, vm, view = window
    view.start_button.invoke()
    pump(root)
    assert vm.game.error is None
    view.on_space_press(SimpleNamespace(widget=root))
    assert vm.controller.read_state().upper_lane
    view.on_focus_out(None)
    assert not vm.controller.read_state().upper_lane
    first = vm.game
    view.show_setup()
    assert not first.thread.is_alive()
    assert set(view._callbacks) == {"status"}
    choose(view, "label")
    assert view.label_preview.get() == "Latest label: eyesOpen"
    user.rename_stream("Classifier", "Renamed classifier")
    assert view.source_combo.get() == "Renamed classifier"
    control.stop()
    pump(root)
    assert view.start_button.instate(["disabled"])
    control.start()
    pump(root)
    assert not view.start_button.instate(["disabled"])
    view.start_button.invoke()
    pump(root)
    assert vm.controller.read_state().upper_lane
    view.on_space_release(SimpleNamespace(widget=root))
    assert vm.controller.read_state().upper_lane
    view.on_close()
    assert source.is_alive() and control.is_alive()
    assert view.closed and not view._callbacks


def test_alpha_editing_restart_input_loss_and_source_removal(window):
    root, user, source, control, vm, view = window
    choose(view, "alpha")
    assert view.channel_combo['values'] == ('Channel 1', 'Channel 2')
    view.channel_combo.current(1)
    view._change_channel()
    view.start_button.invoke()
    pump(root)
    assert vm.channel_index == 1
    assert view._threshold_initialized
    original = vm.controller.read_state().threshold
    assert original > 0
    view.threshold_text.set(str(original / 2))
    view.threshold_entry.event_generate("<FocusOut>")
    pump(root)
    assert vm.controller.read_state().upper_lane
    view.threshold_text.set("nan")
    view.apply_threshold()
    assert "previous value retained" in view.threshold_error.get()
    assert vm.controller.read_state().threshold == original / 2
    view.on_restart_key(SimpleNamespace(widget=view.threshold_entry))
    assert not vm.game._restart_event.is_set()
    vm.restart()
    pump(root)
    assert vm.controller.read_state().threshold == original / 2
    source.stop()
    pump(root)
    assert vm.game.paused
    assert "Paused" in view.input_status.get()
    source.start()
    pump(root)
    assert not vm.game.paused
    user.remove_stream_by_name(source.stream_name)
    pump(root)
    assert vm.game.paused
    assert "Change controller" in view.input_status.get()
    view.show_setup()
    assert not view.source_combo.get()
    assert view.start_button.instate(["disabled"])


def test_external_window_destruction_cleans_threads_and_subscriptions(window):
    root, user, source, control, vm, view = window
    choose(view, "label")
    view.start_run()
    pump(root)
    controller = vm.controller
    game = vm.game
    root.destroy()
    assert view.closed
    assert not controller.is_alive()
    assert not game.thread.is_alive()
    assert vm not in user.observers
    assert source.is_alive() and control.is_alive()


def test_application_launch_is_singleton_and_shutdown_closes_runner(window):
    from main import open_game, shutdown_app

    root, user, source, control, vm, view = window
    child = open_game(root, user)
    assert open_game(root, user) is child
    child.start_run()
    pump(root)
    game = child.view_model.game
    saved = []
    save_model = SimpleNamespace(dump=lambda model: saved.append(model))
    shutdown_app(root, user, save_model, {})
    assert child.closed and view.closed
    assert not game.thread.is_alive()
    assert not source.is_alive() and not control.is_alive()
    assert saved == [user]
