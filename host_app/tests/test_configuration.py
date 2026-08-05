import json

import pytest

from streamdeck_monitor.infrastructure.configuration import (
    ConfigurationError,
    load_settings,
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
    path.write_text(
        '{"serial":{"scan_interval_seconds":"fast"}}', encoding="utf-8"
    )
    with pytest.raises(ConfigurationError):
        load_settings(path)
