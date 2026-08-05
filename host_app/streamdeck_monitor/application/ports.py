from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol, Sequence

from streamdeck_monitor.domain.messages import DeviceMessage


class ConnectionError(RuntimeError):
    pass


class LineConnection(Protocol):
    @property
    def port_name(self) -> str: ...

    def write_line(self, line: str) -> None: ...

    def read_line(self) -> str | None: ...

    def close(self) -> None: ...


class SerialProvider(Protocol):
    def available_ports(self) -> Sequence[str]: ...

    def open(self, port: str, baud_rate: int) -> LineConnection: ...


class ProtocolCodec(Protocol):
    def encode_probe(self) -> str: ...

    def decode_line(self, line: str) -> DeviceMessage: ...


class RuntimeClock(Protocol):
    def now(self) -> datetime: ...

    def monotonic(self) -> float: ...

    def sleep(self, seconds: float) -> None: ...


class LogSink(Protocol):
    def emit(
        self,
        level: str,
        event: str,
        timestamp: datetime,
        details: Mapping[str, object],
    ) -> None: ...
