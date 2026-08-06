from __future__ import annotations

import os
import threading
from typing import Callable

from streamdeck_monitor.application.monitor import DeckMonitor
from streamdeck_monitor.application.settings import GuiConfiguration
from streamdeck_monitor.infrastructure.action_dispatcher import QueuedActionDispatcher
from streamdeck_monitor.infrastructure.action_executors import (
    DryRunActionExecutor,
    WindowsActionExecutor,
)
from streamdeck_monitor.infrastructure.event_sink import (
    CompositeLogSink,
    EventStreamSink,
    LogEntry,
)
from streamdeck_monitor.infrastructure.logging_adapter import CombinedLoggingSink
from streamdeck_monitor.infrastructure.protocol import JsonProtocolCodec
from streamdeck_monitor.infrastructure.runtime import SystemClock
from streamdeck_monitor.infrastructure.serial_adapter import PySerialProvider

MonitorFactory = Callable[[GuiConfiguration, EventStreamSink], DeckMonitor]


class RuntimeService:
    """Owns the serial monitor and action worker used by the GUI."""

    def __init__(
        self,
        configuration: GuiConfiguration,
        monitor_factory: MonitorFactory | None = None,
    ) -> None:
        self._configuration = configuration
        self._monitor_factory = monitor_factory or _build_monitor
        self._events = EventStreamSink(configuration.ui.recent_event_limit)
        self._monitor: DeckMonitor | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    @property
    def events(self) -> EventStreamSink:
        return self._events

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def subscribe(self, callback: Callable[[LogEntry], None]) -> Callable[[], None]:
        return self._events.subscribe(callback)

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            monitor = self._monitor_factory(self._configuration, self._events)
            self._monitor = monitor
            self._thread = threading.Thread(
                target=self._run_monitor,
                args=(monitor,),
                name="streamdeck-monitor",
                daemon=True,
            )
            self._thread.start()

    def stop(self, timeout: float = 3.0) -> bool:
        with self._lock:
            monitor = self._monitor
            thread = self._thread
        if monitor is None or thread is None:
            return True
        monitor.stop()
        thread.join(timeout=timeout)
        stopped = not thread.is_alive()
        if stopped:
            monitor.close()
            with self._lock:
                if self._monitor is monitor:
                    self._monitor = None
                    self._thread = None
        return stopped

    def restart(self, configuration: GuiConfiguration) -> bool:
        if not self.stop():
            return False
        with self._lock:
            self._configuration = configuration
        self.start()
        return True

    def apply_profile(self, configuration: GuiConfiguration) -> None:
        with self._lock:
            self._configuration = configuration
            monitor = self._monitor
        if monitor is not None:
            monitor.update_bindings(configuration.active_profile.bindings)

    def pause_actions(self) -> None:
        with self._lock:
            monitor = self._monitor
        if monitor is not None:
            monitor.pause_actions()

    def resume_actions(self) -> None:
        with self._lock:
            monitor = self._monitor
        if monitor is not None:
            monitor.resume_actions()

    def test_binding(self, binding_id: str) -> bool:
        with self._lock:
            monitor = self._monitor
            bindings = self._configuration.active_profile.bindings
        binding = next((item for item in bindings if item.id == binding_id), None)
        if monitor is None or binding is None:
            return False
        monitor.test_action(binding)
        return True

    def _run_monitor(self, monitor: DeckMonitor) -> None:
        try:
            monitor.run_forever()
        except Exception as error:  # keep an unexpected worker failure visible in GUI
            self._events.emit(
                "ERROR",
                "runtime_failed",
                SystemClock().now(),
                {"reason": str(error)},
            )


def _build_monitor(
    configuration: GuiConfiguration, event_sink: EventStreamSink
) -> DeckMonitor:
    clock = SystemClock()
    sink = CompositeLogSink(CombinedLoggingSink(configuration.logging), event_sink)
    executor = WindowsActionExecutor() if os.name == "nt" else DryRunActionExecutor()
    dispatcher = QueuedActionDispatcher(
        executor=executor,
        sink=sink,
        clock=clock,
        queue_size=configuration.queue_size,
    )
    return DeckMonitor(
        settings=configuration.serial,
        provider=PySerialProvider(),
        codec=JsonProtocolCodec(),
        clock=clock,
        sink=sink,
        bindings=configuration.active_profile.bindings,
        dispatcher=dispatcher,
    )
