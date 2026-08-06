import json

from streamdeck_monitor.infrastructure.config_repository import ConfigurationRepository


def test_creates_default_configuration_in_repository(tmp_path) -> None:
    path = tmp_path / "config.json"
    repository = ConfigurationRepository(path)

    configuration = repository.load_or_create()

    assert path.exists()
    assert repository.load() == configuration
    assert configuration.active_profile.name == "Padrão"


def test_save_creates_restorable_backup(tmp_path) -> None:
    repository = ConfigurationRepository(tmp_path / "config.json")
    original = repository.load_or_create()
    updated = type(original)(
        active_profile_id=original.active_profile_id,
        serial=original.serial,
        logging=original.logging,
        queue_size=32,
        ui=original.ui,
        profiles=original.profiles,
    )

    repository.save(updated)
    restored = repository.restore_backup()

    assert repository.backup_path.exists()
    assert restored.queue_size == original.queue_size
    assert repository.load() == original


def test_load_migrates_legacy_file(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "serial": {"port": "auto", "baud_rate": 115200},
                "actions": {"bindings": []},
            }
        ),
        encoding="utf-8",
    )

    configuration = ConfigurationRepository(path).load()

    assert configuration.schema_version == 2
    assert configuration.active_profile.name == "Padrão"


def test_exports_and_imports_profile_with_unique_identity(tmp_path) -> None:
    repository = ConfigurationRepository(tmp_path / "config.json")
    configuration = repository.load_or_create()
    export_path = tmp_path / "profile.json"
    repository.export_profile(configuration.active_profile, export_path)

    imported = repository.import_profile(export_path, configuration)

    assert len(imported.profiles) == 2
    assert imported.active_profile.id != configuration.active_profile.id
    assert imported.active_profile.name == "Padrão (2)"


def test_imports_legacy_file_as_profile_without_overwriting_globals(tmp_path) -> None:
    repository = ConfigurationRepository(tmp_path / "config.json")
    configuration = repository.load_or_create()
    legacy = tmp_path / "legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "serial": {"port": "COM99"},
                "actions": {"bindings": []},
            }
        ),
        encoding="utf-8",
    )

    imported = repository.import_profile(legacy, configuration)

    assert imported.serial == configuration.serial
    assert imported.active_profile.name == "Importado"
