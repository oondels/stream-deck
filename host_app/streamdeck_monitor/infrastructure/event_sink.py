from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
import threading
from typing import Callable, Mapping

from streamdeck_monitor.application.ports import LogSink


@dataclass(frozen=True, slots=True)
class LogEntry:
    level: str
    event: str
    timestamp: datetime
    details: dict[str, object]


class CompositeLogSink:
    def __init__(self, *sinks: LogSink) -> None:
        self._sinks = sinks

    def emit(
        self,
        level: str,
        event: str,
        timestamp: datetime,
        details: Mapping[str, object],
    ) -> None:
        for sink in self._sinks:
            sink.emit(level, event, timestamp, details)


class EventStreamSink:
    def __init__(self, limit: int = 200) -> None:
        self._limit = limit
        self._entries: deque[LogEntry] = deque(maxlen=limit)
        self._subscribers: list[Callable[[LogEntry], None]] = []
        self._lock = threading.Lock()

    @property
    def limit(self) -> int:
        return self._limit

    def subscribe(self, callback: Callable[[LogEntry], None]) -> Callable[[], None]:
        with self._lock:
            self._subscribers.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def snapshot(self) -> tuple[LogEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    def emit(
        self,
        level: str,
        event: str,
        timestamp: datetime,
        details: Mapping[str, object],
    ) -> None:
        entry = LogEntry(level, event, timestamp, dict(details))
        with self._lock:
            self._entries.append(entry)
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            subscriber(entry)
