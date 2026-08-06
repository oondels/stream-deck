from __future__ import annotations

from pathlib import Path
from uuid import uuid4

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
    ControlAppearance,
    Profile,
)


def default_profile(profile_id: str | None = None, name: str = "Padrão") -> Profile:
    return Profile(
        id=profile_id or str(uuid4()),
        name=name,
        display=(
            ControlAppearance("key_1", "Anterior", "previous", "#2563EB"),
            ControlAppearance("key_2", "Reproduzir", "play", "#16A34A"),
            ControlAppearance("key_3", "Próxima", "next", "#2563EB"),
            ControlAppearance("key_4", "Parar", "stop", "#DC2626"),
            ControlAppearance("key_5", "Área de trabalho", "desktop", "#0891B2"),
            ControlAppearance("key_6", "Calculadora", "calculator", "#EA580C"),
            ControlAppearance("key_7", "YouTube", "globe", "#DC2626"),
            ControlAppearance("encoder", "Volume", "volume", "#7C3AED"),
        ),
        bindings=(
            Binding("previous-track", "key_1", "press", MediaAction("previous_track")),
            Binding("play-pause", "key_2", "press", MediaAction("play_pause")),
            Binding("next-track", "key_3", "press", MediaAction("next_track")),
            Binding("stop", "key_4", "press", MediaAction("stop")),
            Binding("show-desktop", "key_5", "press", HotkeyAction(("win", "d"))),
            Binding("calculator", "key_6", "press", LaunchAction("calc.exe")),
            Binding(
                "youtube",
                "key_7",
                "press",
                OpenUrlAction("https://www.youtube.com"),
            ),
            Binding("volume-down", "encoder_ccw", "rotate", MediaAction("volume_down")),
            Binding("volume-up", "encoder_cw", "rotate", MediaAction("volume_up")),
            Binding(
                "volume-mute", "encoder_press", "press", MediaAction("volume_mute")
            ),
        ),
    )


def default_gui_configuration(
    config_directory: Path, profile_id: str | None = None
) -> GuiConfiguration:
    profile = default_profile(profile_id)
    return GuiConfiguration(
        active_profile_id=profile.id,
        serial=SerialSettings(),
        logging=LoggingSettings(file=str(config_directory / "logs" / "events.jsonl")),
        queue_size=64,
        ui=UiSettings(),
        profiles=(profile,),
    )
