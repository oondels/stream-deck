from __future__ import annotations

import threading


class MonitorControl:
    def __init__(self) -> None:
        self._stop = threading.Event()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def stop(self) -> None:
        self._stop.set()

    def wait(self, seconds: float) -> bool:
        return self._stop.wait(seconds)


class ActionGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._paused = False

    @property
    def paused(self) -> bool:
        with self._lock:
            return self._paused

    def pause(self) -> None:
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        with self._lock:
            self._paused = False
