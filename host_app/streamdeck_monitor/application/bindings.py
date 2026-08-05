from __future__ import annotations

from streamdeck_monitor.domain.actions import Binding


class BindingResolver:
    def __init__(self, bindings: tuple[Binding, ...]) -> None:
        self._bindings = {
            (binding.control, binding.event): binding for binding in bindings
        }

    def resolve(self, control: str, event: str) -> Binding | None:
        return self._bindings.get((control, event))
