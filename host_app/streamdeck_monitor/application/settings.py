from dataclasses import dataclass

from streamdeck_monitor.domain.actions import Binding


@dataclass(frozen=True, slots=True)
class SerialSettings:
    port: str | None = None
    baud_rate: int = 115200
    scan_interval_seconds: float = 2.0
    handshake_timeout_seconds: float = 2.5


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    level: str = "INFO"
    file: str = "host_app/logs/events.jsonl"
    max_bytes: int = 1_048_576
    backup_count: int = 5


@dataclass(frozen=True, slots=True)
class ActionsSettings:
    bindings: tuple[Binding, ...] = ()
    queue_size: int = 64


@dataclass(frozen=True, slots=True)
class AppSettings:
    serial: SerialSettings = SerialSettings()
    logging: LoggingSettings = LoggingSettings()
    actions: ActionsSettings = ActionsSettings()
