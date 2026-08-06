from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.gui.action_editor import ActionEditor
from streamdeck_monitor.gui.deck_widget import DeckWidget
from streamdeck_monitor.gui.main_window import MainWindow
from streamdeck_monitor.infrastructure.config_repository import ConfigurationRepository
from streamdeck_monitor.infrastructure.event_sink import LogEntry


class FakeRuntime:
    def __init__(self) -> None:
        self.callback = None
        self.applied = []
        self.tested = []
        self.paused = False
        self.stopped = False

    def subscribe(self, callback):
        self.callback = callback
        return lambda: setattr(self, "callback", None)

    def apply_profile(self, configuration) -> None:
        self.applied.append(configuration)

    def pause_actions(self) -> None:
        self.paused = True

    def resume_actions(self) -> None:
        self.paused = False

    def test_binding(self, binding_id: str) -> bool:
        self.tested.append(binding_id)
        return True

    def stop(self) -> bool:
        self.stopped = True
        return True

    def emit(self, record_event: str, **details) -> None:
        assert self.callback is not None
        self.callback(
            LogEntry("INFO", record_event, datetime.now(timezone.utc), dict(details))
        )


def test_deck_uses_expected_layout_and_selects_control(qtbot, tmp_path) -> None:
    profile = default_gui_configuration(tmp_path).active_profile
    deck = DeckWidget(profile)
    qtbot.addWidget(deck)

    assert set(deck._cards) == {
        "key_1",
        "key_2",
        "key_3",
        "key_4",
        "key_5",
        "key_6",
        "key_7",
        "encoder",
    }
    qtbot.mouseClick(deck._cards["key_7"], Qt.MouseButton.LeftButton)
    assert deck.selected_control == "key_7"
    assert deck._cards["key_7"].isChecked()


def test_action_editor_removes_binding_when_none_is_selected(qtbot, tmp_path) -> None:
    profile = default_gui_configuration(tmp_path).active_profile
    editor = ActionEditor()
    qtbot.addWidget(editor)
    editor.set_control(profile, "key_1")
    spy = QSignalSpy(editor.profile_changed)

    editor.action_combo.setCurrentIndex(editor.action_combo.findData("none"))

    assert spy.count() == 1
    changed = spy.at(0)[0]
    assert not any(
        binding.control == "key_1" and binding.event == "press"
        for binding in changed.bindings
    )


def test_main_window_persists_changes_and_receives_runtime_events(
    qtbot, tmp_path
) -> None:
    configuration = default_gui_configuration(tmp_path)
    repository = ConfigurationRepository(tmp_path / "config.json")
    repository.save(configuration, create_backup=False)
    runtime = FakeRuntime()
    window = MainWindow(configuration, repository, runtime)
    qtbot.addWidget(window)

    qtbot.mouseClick(window.deck._cards["key_7"], Qt.MouseButton.LeftButton)
    assert window.editor.label_edit.text() == "YouTube"
    window.editor.label_edit.setText("Vídeos")
    window.editor.label_edit.editingFinished.emit()

    assert repository.load().active_profile.display[6].label == "Vídeos"
    assert runtime.applied

    runtime.emit("device_connected", port="COM4", board="esp32-c3", firmware="0.1.0")
    runtime.emit(
        "input",
        port="COM4",
        control="key_7",
        event="press",
        sequence=1,
        uptime_ms=10,
        version=1,
    )

    assert "COM4" in window.connection_label.text()
    assert window.event_table.rowCount() == 2
    assert window.deck._cards["key_7"].property("active") is True
