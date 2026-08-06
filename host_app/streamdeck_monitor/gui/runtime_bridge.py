from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from streamdeck_monitor.application.runtime_service import RuntimeService
from streamdeck_monitor.infrastructure.event_sink import LogEntry


class RuntimeBridge(QObject):
    entry_received = Signal(object)
    connection_changed = Signal(str, object)
    input_received = Signal(str, str)
    pause_changed = Signal(bool)

    def __init__(self, service: RuntimeService) -> None:
        super().__init__()
        self._unsubscribe = service.subscribe(self._on_entry)

    def close(self) -> None:
        self._unsubscribe()

    def _on_entry(self, entry: LogEntry) -> None:
        self.entry_received.emit(entry)
        if entry.event == "device_connected":
            self.connection_changed.emit("connected", entry.details)
        elif entry.event in {"device_searching", "device_disconnected"}:
            self.connection_changed.emit("searching", entry.details)
        elif entry.event in {"monitor_stopped", "runtime_failed"}:
            self.connection_changed.emit("stopped", entry.details)
        elif entry.event == "input":
            self.input_received.emit(
                str(entry.details.get("control", "")),
                str(entry.details.get("event", "")),
            )
        elif entry.event == "actions_paused":
            self.pause_changed.emit(True)
        elif entry.event == "actions_resumed":
            self.pause_changed.emit(False)
