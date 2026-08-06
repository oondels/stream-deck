from __future__ import annotations

from dataclasses import asdict
import re
from typing import Mapping
from uuid import UUID, uuid4

from streamdeck_monitor.application.defaults import default_profile
from streamdeck_monitor.application.settings import (
    GuiConfiguration,
    LoggingSettings,
    SerialSettings,
    UiSettings,
)
from streamdeck_monitor.domain.actions import (
    Binding,
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)
from streamdeck_monitor.domain.profiles import (
    PHYSICAL_CONTROLS,
    SCHEMA_VERSION,
    ControlAppearance,
    Profile,
)
from streamdeck_monitor.infrastructure.configuration import (
    ConfigurationError,
    _build_actions,
    _build_settings,
    _validate,
)

ICONS = {
    "none",
    "previous",
    "play",
    "next",
    "stop",
    "desktop",
    "calculator",
    "globe",
    "volume",
    "mute",
    "keyboard",
    "application",
}
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def decode_gui_configuration(raw: object) -> GuiConfiguration:
    if not isinstance(raw, Mapping):
        raise ConfigurationError("configuration root must be an object")
    allowed = {
        "schema_version",
        "active_profile_id",
        "serial",
        "logging",
        "actions",
        "ui",
        "profiles",
    }
    _reject_unknown(raw, allowed, "configuration")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ConfigurationError(
            f"unsupported configuration schema: {raw.get('schema_version')!r}"
        )

    serial = _build_settings(SerialSettings, raw.get("serial", {}), "serial")
    if serial.port == "auto":
        serial = SerialSettings(
            port=None,
            baud_rate=serial.baud_rate,
            scan_interval_seconds=serial.scan_interval_seconds,
            handshake_timeout_seconds=serial.handshake_timeout_seconds,
        )
    logging = _build_settings(LoggingSettings, raw.get("logging", {}), "logging")
    _validate(serial, logging)
    queue_size = _decode_queue_settings(raw.get("actions", {}))
    ui = _decode_ui(raw.get("ui", {}))

    raw_profiles = raw.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ConfigurationError("profiles must be a non-empty array")
    profiles = tuple(
        _decode_profile(item, queue_size, index)
        for index, item in enumerate(raw_profiles)
    )
    ids = [profile.id for profile in profiles]
    names = [profile.name.casefold() for profile in profiles]
    if len(ids) != len(set(ids)):
        raise ConfigurationError("profile ids must be unique")
    if len(names) != len(set(names)):
        raise ConfigurationError("profile names must be unique")

    active_profile_id = _string(raw.get("active_profile_id"), "active_profile_id")
    if active_profile_id not in set(ids):
        raise ConfigurationError("active_profile_id does not identify a profile")
    return GuiConfiguration(
        active_profile_id=active_profile_id,
        serial=serial,
        logging=logging,
        queue_size=queue_size,
        ui=ui,
        profiles=profiles,
    )


def encode_gui_configuration(configuration: GuiConfiguration) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "active_profile_id": configuration.active_profile_id,
        "serial": _encode_serial(configuration.serial),
        "logging": asdict(configuration.logging),
        "actions": {"queue_size": configuration.queue_size},
        "ui": asdict(configuration.ui),
        "profiles": [encode_profile(profile) for profile in configuration.profiles],
    }


def encode_profile(profile: Profile) -> dict[str, object]:
    return {
        "id": profile.id,
        "name": profile.name,
        "display": {
            appearance.control: {
                "label": appearance.label,
                "icon": appearance.icon,
                "color": appearance.color,
            }
            for appearance in profile.display
        },
        "bindings": [_encode_binding(binding) for binding in profile.bindings],
    }


def decode_profile(raw: object, queue_size: int = 64) -> Profile:
    return _decode_profile(raw, queue_size, 0)


def migrate_legacy_configuration(
    raw: object, profile_id: str | None = None, profile_name: str = "Importado"
) -> tuple[SerialSettings, LoggingSettings, int, Profile]:
    if not isinstance(raw, Mapping):
        raise ConfigurationError("configuration root must be an object")
    unknown = set(raw) - {"serial", "logging", "actions"}
    if unknown:
        raise ConfigurationError(f"unknown configuration sections: {sorted(unknown)}")
    serial = _build_settings(SerialSettings, raw.get("serial", {}), "serial")
    if serial.port == "auto":
        serial = SerialSettings(
            port=None,
            baud_rate=serial.baud_rate,
            scan_interval_seconds=serial.scan_interval_seconds,
            handshake_timeout_seconds=serial.handshake_timeout_seconds,
        )
    logging = _build_settings(LoggingSettings, raw.get("logging", {}), "logging")
    _validate(serial, logging)
    actions = _build_actions(raw.get("actions", {}))
    base = default_profile(profile_id or str(uuid4()), profile_name)
    profile = Profile(base.id, base.name, base.display, actions.bindings)
    return serial, logging, actions.queue_size, profile


def _decode_profile(raw: object, queue_size: int, index: int) -> Profile:
    label = f"profiles[{index}]"
    if not isinstance(raw, Mapping):
        raise ConfigurationError(f"{label} must be an object")
    _reject_unknown(raw, {"id", "name", "display", "bindings"}, label)
    profile_id = _string(raw.get("id"), f"{label}.id")
    try:
        UUID(profile_id)
    except ValueError as error:
        raise ConfigurationError(f"{label}.id must be a UUID") from error
    name = _string(raw.get("name"), f"{label}.name").strip()
    if not name:
        raise ConfigurationError(f"{label}.name must not be blank")
    display = _decode_display(raw.get("display"), label)
    bindings_raw = raw.get("bindings", [])
    actions = _build_actions({"queue_size": queue_size, "bindings": bindings_raw})
    return Profile(profile_id, name, display, actions.bindings)


def _decode_display(raw: object, label: str) -> tuple[ControlAppearance, ...]:
    if not isinstance(raw, Mapping):
        raise ConfigurationError(f"{label}.display must be an object")
    if set(raw) != set(PHYSICAL_CONTROLS):
        raise ConfigurationError(
            f"{label}.display must define exactly {sorted(PHYSICAL_CONTROLS)}"
        )
    result = []
    for control in PHYSICAL_CONTROLS:
        item = raw[control]
        item_label = f"{label}.display.{control}"
        if not isinstance(item, Mapping):
            raise ConfigurationError(f"{item_label} must be an object")
        _reject_unknown(item, {"label", "icon", "color"}, item_label)
        text = _string(item.get("label"), f"{item_label}.label").strip()
        icon = _string(item.get("icon"), f"{item_label}.icon")
        color = _string(item.get("color"), f"{item_label}.color").upper()
        if not text:
            raise ConfigurationError(f"{item_label}.label must not be blank")
        if icon not in ICONS:
            raise ConfigurationError(f"{item_label}.icon is unsupported")
        if not COLOR_PATTERN.fullmatch(color):
            raise ConfigurationError(f"{item_label}.color must use #RRGGBB")
        result.append(ControlAppearance(control, text, icon, color))
    return tuple(result)


def _decode_ui(raw: object) -> UiSettings:
    if not isinstance(raw, Mapping):
        raise ConfigurationError("ui must be an object")
    _reject_unknown(
        raw,
        {"start_with_windows", "close_to_tray", "theme", "recent_event_limit"},
        "ui",
    )
    start = raw.get("start_with_windows", False)
    close = raw.get("close_to_tray", True)
    theme = raw.get("theme", "dark")
    limit = raw.get("recent_event_limit", 200)
    if type(start) is not bool or type(close) is not bool:
        raise ConfigurationError("ui boolean settings are invalid")
    if theme != "dark":
        raise ConfigurationError("ui.theme must be 'dark'")
    if type(limit) is not int or not 10 <= limit <= 10_000:
        raise ConfigurationError("ui.recent_event_limit must be between 10 and 10000")
    return UiSettings(start, close, theme, limit)


def _decode_queue_settings(raw: object) -> int:
    if not isinstance(raw, Mapping):
        raise ConfigurationError("actions must be an object")
    _reject_unknown(raw, {"queue_size"}, "actions")
    value = raw.get("queue_size", 64)
    if type(value) is not int or value <= 0:
        raise ConfigurationError("actions.queue_size must be a positive integer")
    return value


def _encode_serial(settings: SerialSettings) -> dict[str, object]:
    return {
        "port": settings.port or "auto",
        "baud_rate": settings.baud_rate,
        "scan_interval_seconds": settings.scan_interval_seconds,
        "handshake_timeout_seconds": settings.handshake_timeout_seconds,
    }


def _encode_binding(binding: Binding) -> dict[str, object]:
    action = binding.action
    if isinstance(action, MediaAction):
        encoded_action: dict[str, object] = {"type": "media", "command": action.command}
    elif isinstance(action, HotkeyAction):
        encoded_action = {"type": "hotkey", "keys": list(action.keys)}
    elif isinstance(action, LaunchAction):
        encoded_action = {
            "type": "launch",
            "executable": action.executable,
            "args": list(action.args),
        }
    elif isinstance(action, OpenUrlAction):
        encoded_action = {"type": "open_url", "url": action.url}
    else:  # pragma: no cover - Action union is exhaustive
        raise TypeError(f"unsupported action: {type(action).__name__}")
    return {
        "id": binding.id,
        "control": binding.control,
        "event": binding.event,
        "action": encoded_action,
    }


def _reject_unknown(
    raw: Mapping[object, object], allowed: set[str], label: str
) -> None:
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigurationError(f"unknown {label} fields: {sorted(unknown)}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f"{label} must be a non-empty string")
    return value
