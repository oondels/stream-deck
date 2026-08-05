from __future__ import annotations

from dataclasses import asdict

from streamdeck_monitor.application.ports import (
    ConnectionError,
    LineConnection,
    LogSink,
    ProtocolCodec,
    RuntimeClock,
    SerialProvider,
)
from streamdeck_monitor.application.settings import SerialSettings
from streamdeck_monitor.domain.messages import DeviceHello, InputEvent, ProtocolError


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
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._codec = codec
        self._clock = clock
        self._sink = sink
        self._sequences = SequenceTracker()

    def run_forever(self) -> None:
        self._log("INFO", "monitor_started", port=self._settings.port or "auto")
        while True:
            connection = self.discover_once()
            if connection is None:
                self._clock.sleep(self._settings.scan_interval_seconds)
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

    def discover_once(self) -> LineConnection | None:
        ports = (
            [self._settings.port]
            if self._settings.port
            else list(self._provider.available_ports())
        )
        for port in ports:
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
        while self._clock.monotonic() < deadline:
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
        while True:
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
        if sequence_issue is not None:
            event_name, details = sequence_issue
            self._log("WARNING", event_name, port=port, **details)
        self._log("INFO", "input", port=port, **asdict(message))

    def _log(self, level: str, record_type: str, **details: object) -> None:
        self._sink.emit(level, record_type, self._clock.now(), details)
