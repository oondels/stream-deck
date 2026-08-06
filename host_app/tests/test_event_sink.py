from datetime import datetime, timezone

from streamdeck_monitor.infrastructure.event_sink import (
    CompositeLogSink,
    EventStreamSink,
)


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, level, event, timestamp, details):
        self.events.append(event)


def test_composite_forwards_to_all_sinks() -> None:
    first = Sink()
    second = Sink()

    CompositeLogSink(first, second).emit(
        "INFO", "connected", datetime.now(timezone.utc), {}
    )

    assert first.events == ["connected"]
    assert second.events == ["connected"]


def test_event_stream_limits_history_and_notifies_subscribers() -> None:
    stream = EventStreamSink(limit=2)
    received = []
    unsubscribe = stream.subscribe(received.append)
    timestamp = datetime.now(timezone.utc)

    stream.emit("INFO", "one", timestamp, {"value": 1})
    stream.emit("INFO", "two", timestamp, {})
    unsubscribe()
    stream.emit("INFO", "three", timestamp, {})

    assert [entry.event for entry in received] == ["one", "two"]
    assert [entry.event for entry in stream.snapshot()] == ["two", "three"]
