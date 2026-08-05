from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Mapping, TypeVar
from urllib.parse import urlparse

from streamdeck_monitor.application.settings import (
    ActionsSettings,
    AppSettings,
    LoggingSettings,
    SerialSettings,
)
from streamdeck_monitor.domain.actions import (
    Action,
    Binding,
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)
from streamdeck_monitor.domain.messages import BUTTON_CONTROLS, ROTATION_CONTROLS

T = TypeVar("T", SerialSettings, LoggingSettings)

MEDIA_COMMANDS = {
    "previous_track",
    "play_pause",
    "next_track",
    "stop",
    "volume_up",
    "volume_down",
    "volume_mute",
}
NAMED_KEYS = {
    "ctrl",
    "alt",
    "shift",
    "win",
    "enter",
    "escape",
    "tab",
    "space",
    "backspace",
    "delete",
    "home",
    "end",
    "page_up",
    "page_down",
    "left",
    "right",
    "up",
    "down",
}
ALLOWED_KEYS = (
    NAMED_KEYS
    | {chr(value) for value in range(ord("a"), ord("z") + 1)}
    | {str(value) for value in range(10)}
    | {f"f{value}" for value in range(1, 25)}
)


class ConfigurationError(ValueError):
    pass


def load_settings(path: str | Path) -> AppSettings:
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"cannot read configuration {config_path}: {error}"
        ) from error
    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be an object")
    unknown_root = set(raw) - {"serial", "logging", "actions"}
    if unknown_root:
        raise ConfigurationError(
            f"unknown configuration sections: {sorted(unknown_root)}"
        )

    serial = _build_settings(SerialSettings, raw.get("serial", {}), "serial")
    logging = _build_settings(LoggingSettings, raw.get("logging", {}), "logging")
    actions = _build_actions(raw.get("actions", {}))
    if serial.port == "auto":
        serial = SerialSettings(
            port=None,
            baud_rate=serial.baud_rate,
            scan_interval_seconds=serial.scan_interval_seconds,
            handshake_timeout_seconds=serial.handshake_timeout_seconds,
        )
    _validate(serial, logging)
    return AppSettings(serial=serial, logging=logging, actions=actions)


def _build_actions(raw: object) -> ActionsSettings:
    if not isinstance(raw, Mapping):
        raise ConfigurationError("actions must be an object")
    unknown = set(raw) - {"bindings", "queue_size"}
    if unknown:
        raise ConfigurationError(f"unknown actions settings: {sorted(unknown)}")
    queue_size = raw.get("queue_size", 64)
    if type(queue_size) is not int or queue_size <= 0:
        raise ConfigurationError("actions.queue_size must be a positive integer")
    raw_bindings = raw.get("bindings", [])
    if not isinstance(raw_bindings, list):
        raise ConfigurationError("actions.bindings must be an array")
    bindings = tuple(
        _build_binding(item, index) for index, item in enumerate(raw_bindings)
    )
    ids = [binding.id for binding in bindings]
    triggers = [(binding.control, binding.event) for binding in bindings]
    if len(ids) != len(set(ids)):
        raise ConfigurationError("binding ids must be unique")
    if len(triggers) != len(set(triggers)):
        raise ConfigurationError("binding control/event pairs must be unique")
    return ActionsSettings(bindings=bindings, queue_size=queue_size)


def _build_binding(raw: object, index: int) -> Binding:
    label = f"actions.bindings[{index}]"
    if not isinstance(raw, Mapping):
        raise ConfigurationError(f"{label} must be an object")
    _reject_unknown(raw, {"id", "control", "event", "action"}, label)
    binding_id = _non_empty_string(raw.get("id"), f"{label}.id")
    control = _non_empty_string(raw.get("control"), f"{label}.control")
    event = _non_empty_string(raw.get("event"), f"{label}.event")
    if control in BUTTON_CONTROLS:
        if event not in {"press", "release"}:
            raise ConfigurationError(f"{label} has an invalid button event")
    elif control in ROTATION_CONTROLS:
        if event != "rotate":
            raise ConfigurationError(f"{label} has an invalid encoder event")
    else:
        raise ConfigurationError(f"{label} has an unknown control: {control}")
    return Binding(binding_id, control, event, _build_action(raw.get("action"), label))


def _build_action(raw: object, label: str) -> Action:
    action_label = f"{label}.action"
    if not isinstance(raw, Mapping):
        raise ConfigurationError(f"{action_label} must be an object")
    action_type = _non_empty_string(raw.get("type"), f"{action_label}.type")
    if action_type == "media":
        _reject_unknown(raw, {"type", "command"}, action_label)
        command = _non_empty_string(raw.get("command"), f"{action_label}.command")
        if command not in MEDIA_COMMANDS:
            raise ConfigurationError(f"unsupported media command: {command}")
        return MediaAction(command)
    if action_type == "hotkey":
        _reject_unknown(raw, {"type", "keys"}, action_label)
        keys = raw.get("keys")
        if not isinstance(keys, list) or not keys:
            raise ConfigurationError(f"{action_label}.keys must be a non-empty array")
        normalized = tuple(
            _non_empty_string(key, f"{action_label}.keys").lower() for key in keys
        )
        unknown_keys = set(normalized) - ALLOWED_KEYS
        if unknown_keys:
            raise ConfigurationError(f"unsupported hotkey keys: {sorted(unknown_keys)}")
        if len(normalized) != len(set(normalized)):
            raise ConfigurationError(f"{action_label}.keys must not contain duplicates")
        return HotkeyAction(normalized)
    if action_type == "launch":
        _reject_unknown(raw, {"type", "executable", "args"}, action_label)
        executable = _non_empty_string(
            raw.get("executable"), f"{action_label}.executable"
        )
        args = raw.get("args", [])
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise ConfigurationError(f"{action_label}.args must be an array of strings")
        return LaunchAction(executable, tuple(args))
    if action_type == "open_url":
        _reject_unknown(raw, {"type", "url"}, action_label)
        url = _non_empty_string(raw.get("url"), f"{action_label}.url")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError(f"{action_label}.url must be an HTTP(S) URL")
        return OpenUrlAction(url)
    raise ConfigurationError(f"unsupported action type: {action_type}")


def _reject_unknown(
    raw: Mapping[object, object], allowed: set[str], label: str
) -> None:
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigurationError(f"unknown {label} fields: {sorted(unknown)}")


def _non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f"{label} must be a non-empty string")
    return value


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
