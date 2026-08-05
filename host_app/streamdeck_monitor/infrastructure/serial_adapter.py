from __future__ import annotations

from typing import Sequence

import serial
from serial.tools import list_ports

from streamdeck_monitor.application.ports import ConnectionError, LineConnection


class PySerialConnection(LineConnection):
    def __init__(self, port: str, baud_rate: int) -> None:
        self._port = port
        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=0.2,
                write_timeout=0.5,
            )
        except serial.SerialException as error:
            raise ConnectionError(str(error)) from error

    @property
    def port_name(self) -> str:
        return self._port

    def write_line(self, line: str) -> None:
        try:
            self._serial.write((line + "\n").encode("utf-8"))
            self._serial.flush()
        except (serial.SerialException, serial.SerialTimeoutException) as error:
            raise ConnectionError(str(error)) from error

    def read_line(self) -> str | None:
        try:
            raw = self._serial.read_until(expected=b"\n", size=257)
        except serial.SerialException as error:
            raise ConnectionError(str(error)) from error
        if not raw:
            return None
        if len(raw) > 256:
            while raw and not raw.endswith(b"\n"):
                raw = self._serial.read_until(expected=b"\n", size=257)
            return "oversized-message"
        return raw.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()


class PySerialProvider:
    def available_ports(self) -> Sequence[str]:
        return sorted(port.device for port in list_ports.comports())

    def open(self, port: str, baud_rate: int) -> LineConnection:
        return PySerialConnection(port, baud_rate)
