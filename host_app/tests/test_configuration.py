import json

import pytest

from streamdeck_monitor.infrastructure.configuration import (
    ConfigurationError,
    load_settings,
)
from streamdeck_monitor.domain.actions import (
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)


def test_loads_auto_port_and_rotation_settings(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "serial": {"port": "auto", "baud_rate": 115200},
                "logging": {
                    "file": "events.jsonl",
                    "max_bytes": 100,
                    "backup_count": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    settings = load_settings(path)
    assert settings.serial.port is None
    assert settings.logging.max_bytes == 100


def test_rejects_unknown_configuration(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"serial":{"mystery":1}}', encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_settings(path)


def test_rejects_wrong_configuration_types(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"serial":{"scan_interval_seconds":"fast"}}', encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_settings(path)


def test_loads_all_action_types(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "actions": {
                    "queue_size": 8,
                    "bindings": [
                        {
                            "id": "media",
                            "control": "key_1",
                            "event": "press",
                            "action": {"type": "media", "command": "play_pause"},
                        },
                        {
                            "id": "keys",
                            "control": "key_2",
                            "event": "press",
                            "action": {"type": "hotkey", "keys": ["WIN", "D"]},
                        },
                        {
                            "id": "app",
                            "control": "key_3",
                            "event": "press",
                            "action": {
                                "type": "launch",
                                "executable": "calc.exe",
                                "args": ["x"],
                            },
                        },
                        {
                            "id": "site",
                            "control": "encoder_cw",
                            "event": "rotate",
                            "action": {
                                "type": "open_url",
                                "url": "https://example.com",
                            },
                        },
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    actions = load_settings(path).actions

    assert actions.queue_size == 8
    assert actions.bindings[0].action == MediaAction("play_pause")
    assert actions.bindings[1].action == HotkeyAction(("win", "d"))
    assert actions.bindings[2].action == LaunchAction("calc.exe", ("x",))
    assert actions.bindings[3].action == OpenUrlAction("https://example.com")


@pytest.mark.parametrize(
    "bindings",
    [
        [
            {
                "id": "same",
                "control": "key_1",
                "event": "press",
                "action": {"type": "media", "command": "stop"},
            },
            {
                "id": "same",
                "control": "key_2",
                "event": "press",
                "action": {"type": "media", "command": "stop"},
            },
        ],
        [
            {
                "id": "one",
                "control": "key_1",
                "event": "press",
                "action": {"type": "media", "command": "stop"},
            },
            {
                "id": "two",
                "control": "key_1",
                "event": "press",
                "action": {"type": "media", "command": "stop"},
            },
        ],
    ],
)
def test_rejects_duplicate_action_bindings(tmp_path, bindings) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"actions": {"bindings": bindings}}), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_settings(path)


@pytest.mark.parametrize(
    "action",
    [
        {"type": "open_url", "url": "file:///tmp/unsafe"},
        {"type": "hotkey", "keys": ["ctrl", "unsupported"]},
        {"type": "media", "command": "eject"},
        {"type": "launch", "executable": ""},
    ],
)
def test_rejects_unsafe_or_unknown_actions(tmp_path, action) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "actions": {
                    "bindings": [
                        {
                            "id": "bad",
                            "control": "key_1",
                            "event": "press",
                            "action": action,
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError):
        load_settings(path)


def test_example_configuration_is_valid() -> None:
    settings = load_settings("config.example.json")
    assert len(settings.actions.bindings) == 10
