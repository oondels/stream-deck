from __future__ import annotations

from dataclasses import dataclass

from streamdeck_monitor.domain.actions import Binding

SCHEMA_VERSION = 2
KEY_CONTROLS = (
    "key_1",
    "key_2",
    "key_3",
    "key_4",
    "key_5",
    "key_6",
    "key_7",
)
DEFAULT_KEY_ORDER = KEY_CONTROLS
PHYSICAL_CONTROLS = (
    *KEY_CONTROLS,
    "encoder",
)


@dataclass(frozen=True, slots=True)
class ControlAppearance:
    control: str
    label: str
    icon: str
    color: str


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    name: str
    display: tuple[ControlAppearance, ...]
    bindings: tuple[Binding, ...]
