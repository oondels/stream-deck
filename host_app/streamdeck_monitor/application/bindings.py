from __future__ import annotations

import threading

from streamdeck_monitor.domain.actions import Binding


class BindingResolver:
    def __init__(self, bindings: tuple[Binding, ...]) -> None:
        self._bindings = {
            (binding.control, binding.event): binding for binding in bindings
        }

    def resolve(self, control: str, event: str) -> Binding | None:
        return self._bindings.get((control, event))


class BindingStore:
    def __init__(self, bindings: tuple[Binding, ...] = ()) -> None:
        self._lock = threading.Lock()
        self._resolver = BindingResolver(bindings)

    def update(self, bindings: tuple[Binding, ...]) -> None:
        resolver = BindingResolver(bindings)
        with self._lock:
            self._resolver = resolver

    def resolve(self, control: str, event: str) -> Binding | None:
        with self._lock:
            resolver = self._resolver
        return resolver.resolve(control, event)
