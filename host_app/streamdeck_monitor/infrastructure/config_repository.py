from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.application.settings import GuiConfiguration
from streamdeck_monitor.domain.profiles import Profile
from streamdeck_monitor.infrastructure.configuration import ConfigurationError
from streamdeck_monitor.infrastructure.profile_configuration import (
    decode_gui_configuration,
    decode_profile,
    encode_gui_configuration,
    encode_profile,
    migrate_legacy_configuration,
)


def default_config_directory() -> Path:
    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "StreamDeckMini"
    return Path.home() / ".streamdeck-mini"


class ConfigurationRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_directory() / "config.json"

    @property
    def backup_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".bak")

    def load_or_create(self) -> GuiConfiguration:
        if self.path.exists():
            return self.load()
        configuration = default_gui_configuration(self.path.parent)
        self.save(configuration, create_backup=False)
        return configuration

    def load(self) -> GuiConfiguration:
        raw = _read_json(self.path)
        if isinstance(raw, dict) and raw.get("schema_version") is not None:
            return decode_gui_configuration(raw)
        serial, logging, queue_size, profile = migrate_legacy_configuration(
            raw, profile_name="Padrão"
        )
        return GuiConfiguration(
            active_profile_id=profile.id,
            serial=serial,
            logging=logging,
            queue_size=queue_size,
            ui=default_gui_configuration(self.path.parent).ui,
            profiles=(profile,),
        )

    def save(self, configuration: GuiConfiguration, create_backup: bool = True) -> None:
        validated = decode_gui_configuration(encode_gui_configuration(configuration))
        if create_backup and self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.path, self.backup_path)
        _write_json_atomic(self.path, encode_gui_configuration(validated))

    def restore_backup(self) -> GuiConfiguration:
        if not self.backup_path.exists():
            raise ConfigurationError("configuration backup is unavailable")
        configuration = decode_gui_configuration(_read_json(self.backup_path))
        self.save(configuration, create_backup=False)
        return configuration

    def export_backup(self, configuration: GuiConfiguration, target: Path) -> None:
        _write_json_atomic(target, encode_gui_configuration(configuration))

    def import_backup(self, source: Path) -> GuiConfiguration:
        return decode_gui_configuration(_read_json(source))

    def export_profile(self, profile: Profile, target: Path) -> None:
        _write_json_atomic(
            target,
            {
                "schema_version": 2,
                "kind": "streamdeck-profile",
                "profile": encode_profile(profile),
            },
        )

    def import_profile(
        self, source: Path, configuration: GuiConfiguration
    ) -> GuiConfiguration:
        raw = _read_json(source)
        if isinstance(raw, dict) and raw.get("kind") == "streamdeck-profile":
            if raw.get("schema_version") != 2:
                raise ConfigurationError("unsupported profile schema")
            profile = decode_profile(raw.get("profile"), configuration.queue_size)
        elif isinstance(raw, dict) and raw.get("schema_version") is None:
            _, _, _, profile = migrate_legacy_configuration(raw)
        else:
            raise ConfigurationError("file is not an importable profile")

        names = {item.name.casefold() for item in configuration.profiles}
        imported_name = _unique_name(profile.name, names)
        imported = replace(profile, id=str(uuid4()), name=imported_name)
        return replace(
            configuration,
            profiles=(*configuration.profiles, imported),
            active_profile_id=imported.id,
        )


def _unique_name(name: str, existing: set[str]) -> str:
    if name.casefold() not in existing:
        return name
    index = 2
    while f"{name} ({index})".casefold() in existing:
        index += 1
    return f"{name} ({index})"


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"cannot read configuration {path}: {error}"
        ) from error


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise ConfigurationError(
            f"cannot write configuration {path}: {error}"
        ) from error
