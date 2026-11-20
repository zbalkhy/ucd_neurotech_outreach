"""Game-independent input snapshots shared by producers and consumers."""

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ControllerState:
    upper_lane: bool = False
    status: str = "waiting"
    message: str = "Waiting for input"
    power: float | None = None
    threshold: float | None = None
    label: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"


class KeyboardController:
    def __init__(self):
        self._lock = Lock()
        self._state = ControllerState(status="ready", message="Keyboard ready")

    def set_active(self, active: bool) -> None:
        with self._lock:
            self._state = ControllerState(
                upper_lane=active, status="ready", message="Keyboard ready")

    def read_state(self) -> ControllerState:
        with self._lock:
            return self._state
