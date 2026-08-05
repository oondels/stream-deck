from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TypeAlias

PROTOCOL_VERSION = 1
DEVICE_NAME = "stream-deck-mini"

BUTTON_CONTROLS = {*(f"key_{index}" for index in range(1, 8)), "encoder_press"}
ROTATION_CONTROLS = {"encoder_cw", "encoder_ccw"}


class ProtocolError(ValueError):
    """A line was decoded but does not satisfy protocol v1."""


@dataclass(frozen=True, slots=True)
class DeviceHello:
    device: str
    board: str
    firmware: str
    version: int = PROTOCOL_VERSION


@dataclass(frozen=True, slots=True)
class InputEvent:
    control: str
    event: str
    sequence: int
    uptime_ms: int
    version: int = PROTOCOL_VERSION


DeviceMessage: TypeAlias = DeviceHello | InputEvent


def decode_mapping(data: Mapping[str, object]) -> DeviceMessage:
    version = _required_int(data, "v")
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"unsupported protocol version: {version}")

    message_type = _required_string(data, "type")
    if message_type == "hello":
        device = _required_string(data, "device")
        if device != DEVICE_NAME:
            raise ProtocolError(f"unexpected device: {device}")
        return DeviceHello(
            device=device,
            board=_required_string(data, "board"),
            firmware=_required_string(data, "firmware"),
        )

    if message_type == "input":
        control = _required_string(data, "control")
        event = _required_string(data, "event")
        if control in BUTTON_CONTROLS and event not in {"press", "release"}:
            raise ProtocolError(f"event {event!r} is invalid for {control!r}")
        if control in ROTATION_CONTROLS and event != "rotate":
            raise ProtocolError(f"event {event!r} is invalid for {control!r}")
        if control not in BUTTON_CONTROLS | ROTATION_CONTROLS:
            raise ProtocolError(f"unknown control: {control}")
        return InputEvent(
            control=control,
            event=event,
            sequence=_required_int(data, "seq"),
            uptime_ms=_required_int(data, "uptime_ms"),
        )

    raise ProtocolError(f"unknown message type: {message_type}")


def _required_string(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ProtocolError(f"{key!r} must be a non-empty string")
    return value


def _required_int(data: Mapping[str, object], key: str) -> int:
    value = data.get(key)
    if type(value) is not int or value < 0:
        raise ProtocolError(f"{key!r} must be a non-negative integer")
    return value
