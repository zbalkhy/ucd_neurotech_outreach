"""Own one runner session and its temporary input controller."""

from Classes.controllerState import KeyboardController
from Classes.eventClass import EventClass, EventType
from Game.week1_game import InfiniteRunner
from Stream.dataStream import StreamType
from Stream.gameControlStream import (
    ALPHA_WINDOW, GameControlStream, channel_count, latest_label,
    source_chain, stopped_sources,
)


class RunnerViewModel(EventClass):
    def __init__(self, user_model, game_factory=InfiniteRunner):
        super().__init__()
        self.user_model = user_model
        self.game_factory = game_factory
        self.mode = "keyboard"
        self.source = None
        self.active_label = "eyesOpen"
        self.channel_index = 0
        self.invert = False
        self.controller = None
        self.game = None
        self._dependencies = []
        self.subscribe_to_subject(user_model)

    def available_sources(self):
        types = ({StreamType.CONTROL} if self.mode == "label" else
                 {StreamType.FILTER, StreamType.DEVICE, StreamType.SOFTWARE})
        return [source for source in self.user_model.get_streams()
                if source.stream_type in types] if self.mode != "keyboard" else []

    def select_mode(self, mode):
        if mode not in ("keyboard", "label", "alpha"):
            raise ValueError("Choose a controller type")
        self.mode = mode
        self.source = None
        self.channel_index = 0

    def select_source(self, source):
        if source not in self.available_sources():
            raise ValueError("Choose a current inventory source")
        self.source = source
        self.channel_index = 0

    def setup_status(self):
        """Return a blocking launch issue, if any; no controller is created."""
        if self.mode == "keyboard":
            return ""
        if self.source not in self.available_sources():
            return "Choose a current inventory source"
        try:
            stopped = stopped_sources(self.source)
            if stopped:
                return "Start in Inventory: " + ", ".join(stopped)
            if self.mode == "alpha":
                capacity = self.source.data.maxlen
                if capacity is not None and capacity < ALPHA_WINDOW:
                    return "Alpha input needs a buffer of at least 100 samples"
                if not 0 <= self.channel_index < channel_count(self.source):
                    return "Choose an available channel"
        except (ValueError, TypeError) as error:
            return str(error)
        return ""

    def preview_label(self):
        if self.source is None:
            return "Waiting for a source"
        try:
            label = latest_label(self.source)
            return "Waiting for a label" if label is None else label
        except (ValueError, TypeError) as error:
            return str(error)

    def start_run(self):
        if self.game is not None:
            raise ValueError("Return to setup before starting another run")
        issue = self.setup_status()
        if issue:
            raise ValueError(issue)
        if self.mode == "keyboard":
            self.controller = KeyboardController()
        else:
            self.controller = GameControlStream(
                self.source, mode=self.mode, active_label=self.active_label,
                channel_index=self.channel_index, invert=self.invert)
            # Track identity, including registered upstream dependencies.
            inventory = self.user_model.get_streams()
            self._dependencies = [source for source in source_chain(self.source)
                                  if source in inventory]
        try:
            if isinstance(self.controller, GameControlStream):
                self.controller.start()
            self.game = self.game_factory(
                size=(800, 600), fps=80,
                read_controller=self.controller.read_state)
            self.game.start()
        except Exception:
            self.stop_run()
            raise

    def set_keyboard(self, active):
        if isinstance(self.controller, KeyboardController):
            self.controller.set_active(active)

    def restart(self):
        if self.game is not None:
            self.game.request_restart()

    def stop_run(self):
        if self.game is not None:
            self.game.stop()
            self.game = None
        if isinstance(self.controller, GameControlStream):
            self.controller.stop()
        self.controller = None
        self._dependencies = []

    def on_notify(self, eventData, event):
        if event in (EventType.STREAMUPDATE, EventType.STREAMLISTUPDATE,
                     EventType.STREAMTOGGLED):
            if isinstance(self.controller, GameControlStream):
                inventory = self.user_model.get_streams()
                if any(source not in inventory for source in self._dependencies):
                    self.controller.invalidate(
                        "Source removed or replaced. Choose Change controller.")
                else:
                    self.controller.update_once()
            self.notify(None, event)

    def dispose(self):
        self.stop_run()
        super().dispose()
