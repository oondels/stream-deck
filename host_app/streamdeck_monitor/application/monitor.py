from __future__ import annotations

from dataclasses import asdict

from streamdeck_monitor.application.ports import (
    ActionDispatcher,
    ConnectionError,
    LineConnection,
    LogSink,
    ProtocolCodec,
    RuntimeClock,
    SerialProvider,
)
from streamdeck_monitor.application.bindings import BindingStore
from streamdeck_monitor.application.runtime_control import ActionGate, MonitorControl
from streamdeck_monitor.application.settings import SerialSettings
from streamdeck_monitor.domain.actions import Binding
from streamdeck_monitor.domain.messages import DeviceHello, ProtocolError


class SequenceTracker:
    def __init__(self) -> None:
        self._last: int | None = None

    def reset(self) -> None:
        self._last = None

    def observe(self, sequence: int) -> tuple[str, dict[str, int]] | None:
        previous = self._last
        self._last = sequence
        if previous is None or sequence == previous + 1:
            return None
        if sequence <= previous:
            return "sequence_reset", {"previous": previous, "received": sequence}
        return "sequence_gap", {
            "previous": previous,
            "expected": previous + 1,
            "received": sequence,
        }


class DeckMonitor:
    def __init__(
        self,
        settings: SerialSettings,
        provider: SerialProvider,
        codec: ProtocolCodec,
        clock: RuntimeClock,
        sink: LogSink,
        bindings: tuple[Binding, ...] = (),
        dispatcher: ActionDispatcher | None = None,
        binding_store: BindingStore | None = None,
        control: MonitorControl | None = None,
        action_gate: ActionGate | None = None,
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._codec = codec
        self._clock = clock
        self._sink = sink
        self._sequences = SequenceTracker()
        self._bindings = binding_store or BindingStore(bindings)
        self._dispatcher = dispatcher
        self._control = control or MonitorControl()
        self._action_gate = action_gate or ActionGate()

    @property
    def stopped(self) -> bool:
        return self._control.stopped

    def stop(self) -> None:
        self._control.stop()

    def update_bindings(self, bindings: tuple[Binding, ...]) -> None:
        self._bindings.update(bindings)

    def pause_actions(self) -> None:
        self._action_gate.pause()
        self._log("INFO", "actions_paused")

    def resume_actions(self) -> None:
        self._action_gate.resume()
        self._log("INFO", "actions_resumed")

    def test_action(self, binding: Binding) -> None:
        if self._dispatcher is None:
            self._log(
                "WARNING",
                "action_test_unavailable",
                binding_id=binding.id,
                reason="dispatcher_unavailable",
            )
            return
        self._log(
            "INFO",
            "action_test_requested",
            binding_id=binding.id,
            action_type=binding.action.type,
        )
        self._dispatcher.submit(binding)

    def close(self) -> None:
        self.stop()
        if self._dispatcher is not None:
            self._dispatcher.close()

    def run_forever(self) -> None:
        self._log("INFO", "monitor_started", port=self._settings.port or "auto")
        self._log("INFO", "device_searching", port=self._settings.port or "auto")
        while not self._control.stopped:
            connection = self.discover_once()
            if connection is None:
                self._control.wait(self._settings.scan_interval_seconds)
                continue
            try:
                self.monitor_connection(connection)
            except ConnectionError as error:
                self._log(
                    "WARNING",
                    "device_disconnected",
                    port=connection.port_name,
                    reason=str(error),
                )
            finally:
                connection.close()
                self._sequences.reset()
                if not self._control.stopped:
                    self._log(
                        "INFO",
                        "device_searching",
                        port=self._settings.port or "auto",
                    )
        self._log("INFO", "monitor_stopped")

    def discover_once(self) -> LineConnection | None:
        ports = (
            [self._settings.port]
            if self._settings.port
            else list(self._provider.available_ports())
        )
        for port in ports:
            if self._control.stopped:
                return None
            connection: LineConnection | None = None
            try:
                connection = self._provider.open(port, self._settings.baud_rate)
                hello = self._identify(connection)
                if hello is not None:
                    self._sequences.reset()
                    self._log(
                        "INFO",
                        "device_connected",
                        port=port,
                        board=hello.board,
                        firmware=hello.firmware,
                    )
                    return connection
            except ConnectionError as error:
                self._log("DEBUG", "port_rejected", port=port, reason=str(error))
            if connection is not None:
                connection.close()
        return None

    def _identify(self, connection: LineConnection) -> DeviceHello | None:
        deadline = self._clock.monotonic() + self._settings.handshake_timeout_seconds
        next_probe = 0.0
        while not self._control.stopped and self._clock.monotonic() < deadline:
            now = self._clock.monotonic()
            if now >= next_probe:
                connection.write_line(self._codec.encode_probe())
                next_probe = now + 0.5
            line = connection.read_line()
            if line is None:
                continue
            try:
                message = self._codec.decode_line(line)
            except ProtocolError:
                continue
            if isinstance(message, DeviceHello):
                return message
        return None

    def monitor_connection(self, connection: LineConnection) -> None:
        while not self._control.stopped:
            line = connection.read_line()
            if line is None:
                continue
            self.process_line(line, connection.port_name)

    def process_line(self, line: str, port: str) -> None:
        try:
            message = self._codec.decode_line(line)
        except ProtocolError as error:
            self._log("WARNING", "invalid_message", port=port, reason=str(error))
            return

        if isinstance(message, DeviceHello):
            self._sequences.reset()
            self._log(
                "INFO",
                "device_hello",
                port=port,
                board=message.board,
                firmware=message.firmware,
            )
            return

        sequence_issue = self._sequences.observe(message.sequence)
        suppress_action = False
        if sequence_issue is not None:
            event_name, details = sequence_issue
            self._log("WARNING", event_name, port=port, **details)
            suppress_action = event_name == "sequence_reset"
        self._log("INFO", "input", port=port, **asdict(message))

        if self._dispatcher is None:
            return
        binding = self._bindings.resolve(message.control, message.event)
        if binding is None:
            self._log(
                "DEBUG",
                "binding_not_found",
                port=port,
                control=message.control,
                input_event=message.event,
            )
            return
        if self._action_gate.paused:
            self._log(
                "INFO",
                "action_suppressed",
                port=port,
                binding_id=binding.id,
                control=message.control,
                input_event=message.event,
                reason="actions_paused",
            )
            return
        if suppress_action:
            self._log(
                "WARNING",
                "action_suppressed",
                port=port,
                binding_id=binding.id,
                control=message.control,
                input_event=message.event,
                reason="non_monotonic_sequence",
            )
            return
        self._dispatcher.submit(binding)

    def _log(self, level: str, record_type: str, **details: object) -> None:
        self._sink.emit(level, record_type, self._clock.now(), details)
