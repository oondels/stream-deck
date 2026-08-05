from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class MediaAction:
    command: str
    type: str = "media"


@dataclass(frozen=True, slots=True)
class HotkeyAction:
    keys: tuple[str, ...]
    type: str = "hotkey"


@dataclass(frozen=True, slots=True)
class LaunchAction:
    executable: str
    args: tuple[str, ...] = ()
    type: str = "launch"


@dataclass(frozen=True, slots=True)
class OpenUrlAction:
    url: str
    type: str = "open_url"


Action: TypeAlias = MediaAction | HotkeyAction | LaunchAction | OpenUrlAction


@dataclass(frozen=True, slots=True)
class Binding:
    id: str
    control: str
    event: str
    action: Action
