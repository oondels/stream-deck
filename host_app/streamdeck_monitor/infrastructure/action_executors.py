from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import subprocess
from typing import Callable

from streamdeck_monitor.domain.actions import (
    Action,
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)


KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

VK_CODES = {
    "ctrl": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "win": 0x5B,
    "enter": 0x0D,
    "escape": 0x1B,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "page_up": 0x21,
    "page_down": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}
VK_CODES.update({chr(value).lower(): value for value in range(ord("A"), ord("Z") + 1)})
VK_CODES.update({str(value): ord(str(value)) for value in range(10)})
VK_CODES.update({f"f{value}": 0x6F + value for value in range(1, 25)})

MEDIA_VK_CODES = {
    "previous_track": 0xB1,
    "play_pause": 0xB3,
    "next_track": 0xB0,
    "stop": 0xB2,
    "volume_up": 0xAF,
    "volume_down": 0xAE,
    "volume_mute": 0xAD,
}


class DryRunActionExecutor:
    @property
    def success_event(self) -> str:
        return "action_dry_run"

    def execute(self, action: Action) -> None:
        return None


class WindowsActionExecutor:
    def __init__(
        self,
        key_sender: Callable[[int, bool], None] | None = None,
        process_launcher: Callable[[list[str]], object] | None = None,
        url_opener: Callable[[str], object] | None = None,
    ) -> None:
        self._key_sender = key_sender or _send_key
        self._process_launcher = process_launcher or _launch_process
        if url_opener is not None:
            self._url_opener = url_opener
        elif hasattr(os, "startfile"):
            self._url_opener = os.startfile
        else:
            raise RuntimeError("Windows URL opener is unavailable")

    @property
    def success_event(self) -> str:
        return "action_succeeded"

    def execute(self, action: Action) -> None:
        if isinstance(action, MediaAction):
            self._tap(MEDIA_VK_CODES[action.command])
            return
        if isinstance(action, HotkeyAction):
            self._hotkey(action)
            return
        if isinstance(action, LaunchAction):
            self._process_launcher([action.executable, *action.args])
            return
        if isinstance(action, OpenUrlAction):
            self._url_opener(action.url)
            return
        raise TypeError(f"unsupported action: {type(action).__name__}")

    def _tap(self, virtual_key: int) -> None:
        self._key_sender(virtual_key, True)
        self._key_sender(virtual_key, False)

    def _hotkey(self, action: HotkeyAction) -> None:
        pressed: list[int] = []
        try:
            for key in action.keys:
                virtual_key = VK_CODES[key]
                self._key_sender(virtual_key, True)
                pressed.append(virtual_key)
        finally:
            for virtual_key in reversed(pressed):
                self._key_sender(virtual_key, False)


def _launch_process(command: list[str]) -> object:
    return subprocess.Popen(command, shell=False)


def _send_key(virtual_key: int, pressed: bool) -> None:
    if os.name != "nt":
        raise RuntimeError("Windows input API is unavailable")

    ulong_ptr = wintypes.WPARAM

    class KeyboardInput(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ulong_ptr),
        ]

    class MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ulong_ptr),
        ]

    class HardwareInput(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [
            ("ki", KeyboardInput),
            ("mi", MouseInput),
            ("hi", HardwareInput),
        ]

    class Input(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = [("type", wintypes.DWORD), ("value", InputUnion)]

    flags = 0 if pressed else KEYEVENTF_KEYUP
    input_event = Input(
        type=INPUT_KEYBOARD,
        value=InputUnion(ki=KeyboardInput(virtual_key, 0, flags, 0, 0)),
    )
    user32 = ctypes.WinDLL("user32", use_last_error=True)  # type: ignore[attr-defined]
    user32.SendInput.argtypes = (
        wintypes.UINT,
        ctypes.POINTER(Input),
        ctypes.c_int,
    )
    user32.SendInput.restype = wintypes.UINT
    sent = user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(Input))
    if sent != 1:
        raise OSError(ctypes.get_last_error(), "SendInput failed")
