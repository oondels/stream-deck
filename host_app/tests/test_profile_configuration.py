from dataclasses import replace
import json
from uuid import uuid4

import pytest

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.domain.profiles import DEFAULT_KEY_ORDER
from streamdeck_monitor.infrastructure.configuration import (
    ConfigurationError,
    load_settings,
)
from streamdeck_monitor.infrastructure.profile_configuration import (
    decode_gui_configuration,
    encode_gui_configuration,
    migrate_legacy_configuration,
)


def test_round_trips_versioned_configuration(tmp_path) -> None:
    original = default_gui_configuration(tmp_path, str(uuid4()))

    decoded = decode_gui_configuration(encode_gui_configuration(original))

    assert decoded == original
    assert decoded.active_profile.name == "Padrão"
    assert len(decoded.active_profile.bindings) == 10


def test_old_versioned_configuration_uses_default_key_order(tmp_path) -> None:
    configuration = default_gui_configuration(tmp_path, str(uuid4()))
    raw = encode_gui_configuration(configuration)
    raw.pop("key_order")

    decoded = decode_gui_configuration(raw)

    assert decoded.key_order == DEFAULT_KEY_ORDER


@pytest.mark.parametrize(
    "key_order",
    [
        ["key_1"] * 7,
        ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
        [
            "key_1",
            "key_2",
            "key_3",
            "key_4",
            "key_5",
            "key_6",
            "encoder",
        ],
        "key_1,key_2,key_3,key_4,key_5,key_6,key_7",
    ],
)
def test_rejects_invalid_key_order(tmp_path, key_order) -> None:
    raw = encode_gui_configuration(default_gui_configuration(tmp_path))
    raw["key_order"] = key_order

    with pytest.raises(ConfigurationError, match="key_order"):
        decode_gui_configuration(raw)


def test_cli_uses_active_profile_from_versioned_configuration(tmp_path) -> None:
    configuration = default_gui_configuration(tmp_path, str(uuid4()))
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(encode_gui_configuration(configuration)), encoding="utf-8"
    )

    settings = load_settings(path)

    assert settings.actions.bindings == configuration.active_profile.bindings
    assert settings.actions.queue_size == 64


def test_migrates_legacy_bindings_without_changing_action_semantics() -> None:
    _, _, queue_size, profile = migrate_legacy_configuration(
        {
            "serial": {"port": "auto", "baud_rate": 115200},
            "actions": {
                "queue_size": 5,
                "bindings": [
                    {
                        "id": "play",
                        "control": "key_1",
                        "event": "press",
                        "action": {"type": "media", "command": "play_pause"},
                    }
                ],
            },
        },
        profile_id=str(uuid4()),
    )

    assert queue_size == 5
    assert profile.bindings[0].id == "play"
    assert len(profile.display) == 8


@pytest.mark.parametrize(
    "change",
    [
        lambda raw: raw.update(schema_version=99),
        lambda raw: raw.update(active_profile_id=str(uuid4())),
        lambda raw: raw["ui"].update(theme="light"),
        lambda raw: raw["profiles"][0]["display"]["key_1"].update(color="red"),
    ],
)
def test_rejects_invalid_versioned_configuration(tmp_path, change) -> None:
    configuration = default_gui_configuration(tmp_path, str(uuid4()))
    raw = encode_gui_configuration(configuration)
    change(raw)

    with pytest.raises(ConfigurationError):
        decode_gui_configuration(raw)


def test_rejects_duplicate_profile_names(tmp_path) -> None:
    configuration = default_gui_configuration(tmp_path, str(uuid4()))
    duplicate = replace(
        configuration.active_profile,
        id=str(uuid4()),
        name=configuration.active_profile.name.upper(),
    )
    raw = encode_gui_configuration(
        replace(configuration, profiles=(*configuration.profiles, duplicate))
    )

    with pytest.raises(ConfigurationError, match="names"):
        decode_gui_configuration(raw)
