from __future__ import annotations

import threading

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.application.runtime_service import RuntimeService


class FakeMonitor:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.closed = False
        self.bindings = ()
        self.paused = False
        self.tested = []

    def run_forever(self) -> None:
        self.started.set()
        self.release.wait(1)

    def stop(self) -> None:
        self.release.set()

    def close(self) -> None:
        self.closed = True

    def update_bindings(self, bindings) -> None:
        self.bindings = bindings

    def pause_actions(self) -> None:
        self.paused = True

    def resume_actions(self) -> None:
        self.paused = False

    def test_action(self, binding) -> None:
        self.tested.append(binding)


def test_runtime_starts_and_stops_monitor(tmp_path) -> None:
    monitor = FakeMonitor()
    service = RuntimeService(
        default_gui_configuration(tmp_path), lambda configuration, sink: monitor
    )

    service.start()
    assert monitor.started.wait(1)
    assert service.running

    assert service.stop()
    assert monitor.closed
    assert not service.running


def test_runtime_applies_profile_pause_and_manual_test(tmp_path) -> None:
    monitor = FakeMonitor()
    configuration = default_gui_configuration(tmp_path)
    service = RuntimeService(configuration, lambda current, sink: monitor)
    service.start()
    assert monitor.started.wait(1)

    service.apply_profile(configuration)
    service.pause_actions()
    assert monitor.bindings == configuration.active_profile.bindings
    assert monitor.paused

    binding = configuration.active_profile.bindings[0]
    assert service.test_binding(binding.id)
    assert monitor.tested == [binding]

    service.resume_actions()
    assert not monitor.paused
    assert service.stop()


def test_runtime_restart_uses_new_configuration(tmp_path) -> None:
    monitors = [FakeMonitor(), FakeMonitor()]
    calls = []

    def factory(configuration, sink):
        calls.append(configuration)
        return monitors[len(calls) - 1]

    configuration = default_gui_configuration(tmp_path)
    service = RuntimeService(configuration, factory)
    service.start()
    assert monitors[0].started.wait(1)

    assert service.restart(configuration)
    assert monitors[1].started.wait(1)
    assert monitors[0].closed
    assert len(calls) == 2
    assert service.stop()
