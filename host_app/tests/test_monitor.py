from collections import deque
from datetime import datetime, timezone

from streamdeck_monitor.application.monitor import DeckMonitor
from streamdeck_monitor.application.ports import ConnectionError
from streamdeck_monitor.application.settings import SerialSettings
from streamdeck_monitor.infrastructure.protocol import JsonProtocolCodec
from streamdeck_monitor.domain.actions import Binding, MediaAction


class FakeClock:
    def __init__(self) -> None:
        self.elapsed = 0.0

    def now(self) -> datetime:
        return datetime(2026, 8, 4, tzinfo=timezone.utc)

    def monotonic(self) -> float:
        self.elapsed += 0.01
        return self.elapsed

    def sleep(self, seconds: float) -> None:
        self.elapsed += seconds


class FakeConnection:
    def __init__(self, port: str, lines: list[str | None]) -> None:
        self._port = port
        self.lines = deque(lines)
        self.written: list[str] = []
        self.closed = False

    @property
    def port_name(self) -> str:
        return self._port

    def write_line(self, line: str) -> None:
        self.written.append(line)

    def read_line(self) -> str | None:
        if self.lines:
            return self.lines.popleft()
        return None

    def close(self) -> None:
        self.closed = True


class FakeProvider:
    def __init__(self, connections: dict[str, FakeConnection | Exception]) -> None:
        self.connections = connections

    def available_ports(self) -> list[str]:
        return list(self.connections)

    def open(self, port: str, baud_rate: int) -> FakeConnection:
        value = self.connections[port]
        if isinstance(value, Exception):
            raise value
        return value


class FakeSink:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def emit(self, level, event, timestamp, details) -> None:
        self.entries.append(
            {
                "level": level,
                "event": event,
                "timestamp": timestamp,
                "details": dict(details),
            }
        )


class FakeDispatcher:
    def __init__(self):
        self.bindings = []
        self.closed = False

    def submit(self, binding):
        self.bindings.append(binding)

    def close(self):
        self.closed = True


def make_monitor(provider: FakeProvider, sink: FakeSink, clock=None) -> DeckMonitor:
    return DeckMonitor(
        settings=SerialSettings(handshake_timeout_seconds=0.1),
        provider=provider,
        codec=JsonProtocolCodec(),
        clock=clock or FakeClock(),
        sink=sink,
    )


def test_discovers_only_connection_with_valid_handshake() -> None:
    rejected = FakeConnection("COM1", ["garbage"])
    accepted = FakeConnection(
        "COM2",
        [
            '{"v":1,"type":"hello","device":"stream-deck-mini",'
            '"board":"esp32","firmware":"0.1.0"}'
        ],
    )
    sink = FakeSink()
    monitor = make_monitor(FakeProvider({"COM1": rejected, "COM2": accepted}), sink)

    result = monitor.discover_once()

    assert result is accepted
    assert rejected.closed
    assert accepted.written == ['{"v":1,"type":"probe"}']
    assert any(entry["event"] == "device_connected" for entry in sink.entries)


def test_skips_port_that_cannot_be_opened() -> None:
    sink = FakeSink()
    monitor = make_monitor(FakeProvider({"COM1": ConnectionError("busy")}), sink)
    assert monitor.discover_once() is None


def test_logs_input_and_sequence_gap() -> None:
    sink = FakeSink()
    monitor = make_monitor(FakeProvider({}), sink)
    first = (
        '{"v":1,"type":"input","control":"key_1","event":"press",'
        '"seq":1,"uptime_ms":100}'
    )
    third = (
        '{"v":1,"type":"input","control":"encoder_cw","event":"rotate",'
        '"seq":3,"uptime_ms":120}'
    )

    monitor.process_line(first, "COM4")
    monitor.process_line(third, "COM4")

    assert [entry["event"] for entry in sink.entries] == [
        "input",
        "sequence_gap",
        "input",
    ]
    assert sink.entries[1]["details"]["expected"] == 2


def test_invalid_line_is_logged_and_ignored() -> None:
    sink = FakeSink()
    monitor = make_monitor(FakeProvider({}), sink)
    monitor.process_line("not-json", "COM4")
    assert sink.entries[0]["event"] == "invalid_message"


def test_dispatches_binding_but_suppresses_regressive_sequence() -> None:
    sink = FakeSink()
    dispatcher = FakeDispatcher()
    binding = Binding("play", "key_1", "press", MediaAction("play_pause"))
    monitor = DeckMonitor(
        settings=SerialSettings(),
        provider=FakeProvider({}),
        codec=JsonProtocolCodec(),
        clock=FakeClock(),
        sink=sink,
        bindings=(binding,),
        dispatcher=dispatcher,
    )
    first = '{"v":1,"type":"input","control":"key_1","event":"press","seq":2,"uptime_ms":100}'
    regressive = '{"v":1,"type":"input","control":"key_1","event":"press","seq":1,"uptime_ms":120}'

    monitor.process_line(first, "COM4")
    monitor.process_line(regressive, "COM4")

    assert dispatcher.bindings == [binding]
    assert any(entry["event"] == "action_suppressed" for entry in sink.entries)


def test_sequence_gap_still_dispatches_received_event() -> None:
    sink = FakeSink()
    dispatcher = FakeDispatcher()
    binding = Binding("play", "key_1", "press", MediaAction("play_pause"))
    monitor = DeckMonitor(
        settings=SerialSettings(),
        provider=FakeProvider({}),
        codec=JsonProtocolCodec(),
        clock=FakeClock(),
        sink=sink,
        bindings=(binding,),
        dispatcher=dispatcher,
    )

    monitor.process_line(
        '{"v":1,"type":"input","control":"key_1","event":"press","seq":1,"uptime_ms":100}',
        "COM4",
    )
    monitor.process_line(
        '{"v":1,"type":"input","control":"key_1","event":"press","seq":3,"uptime_ms":120}',
        "COM4",
    )

    assert dispatcher.bindings == [binding, binding]
    assert any(entry["event"] == "sequence_gap" for entry in sink.entries)
