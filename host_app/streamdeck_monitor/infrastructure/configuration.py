from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Mapping, TypeVar

from streamdeck_monitor.application.settings import (
    AppSettings,
    LoggingSettings,
    SerialSettings,
)

T = TypeVar("T", SerialSettings, LoggingSettings)


class ConfigurationError(ValueError):
    pass


def load_settings(path: str | Path) -> AppSettings:
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"cannot read configuration {config_path}: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be an object")

    serial = _build_settings(SerialSettings, raw.get("serial", {}), "serial")
    logging = _build_settings(LoggingSettings, raw.get("logging", {}), "logging")
    if serial.port == "auto":
        serial = SerialSettings(
            port=None,
            baud_rate=serial.baud_rate,
            scan_interval_seconds=serial.scan_interval_seconds,
            handshake_timeout_seconds=serial.handshake_timeout_seconds,
        )
    _validate(serial, logging)
    return AppSettings(serial=serial, logging=logging)


def _build_settings(cls: type[T], raw: object, section: str) -> T:
    if not isinstance(raw, Mapping):
        raise ConfigurationError(f"{section} must be an object")
    allowed = {field.name for field in fields(cls)}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigurationError(f"unknown {section} settings: {sorted(unknown)}")
    try:
        return cls(**raw)
    except TypeError as error:
        raise ConfigurationError(f"invalid {section} settings: {error}") from error


def _validate(serial: SerialSettings, logging: LoggingSettings) -> None:
    if serial.port is not None and not isinstance(serial.port, str):
        raise ConfigurationError("serial.port must be 'auto' or a port name")
    if type(serial.baud_rate) is not int or serial.baud_rate != 115200:
        raise ConfigurationError("serial.baud_rate must be 115200 for protocol v1")
    if not _positive_number(serial.scan_interval_seconds) or not _positive_number(
        serial.handshake_timeout_seconds
    ):
        raise ConfigurationError("serial intervals must be positive")
    if not isinstance(logging.level, str) or logging.level.upper() not in {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    }:
        raise ConfigurationError("logging.level is invalid")
    if (
        not isinstance(logging.file, str)
        or not logging.file
        or type(logging.max_bytes) is not int
        or logging.max_bytes <= 0
        or type(logging.backup_count) is not int
        or logging.backup_count < 0
    ):
        raise ConfigurationError("logging file rotation settings are invalid")


def _positive_number(value: object) -> bool:
    return type(value) in {int, float} and value > 0
