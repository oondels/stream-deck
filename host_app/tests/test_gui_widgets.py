from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QByteArray, QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QMessageBox

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.gui.action_editor import ActionEditor
from streamdeck_monitor.gui.deck_widget import CONTROL_MIME_TYPE, DeckWidget
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


def test_deck_reorders_keys_but_keeps_encoder_fixed(qtbot, tmp_path) -> None:
    profile = default_gui_configuration(tmp_path).active_profile
    deck = DeckWidget(profile)
    qtbot.addWidget(deck)
    spy = QSignalSpy(deck.key_order_changed)

    deck.set_reorder_enabled(True)
    assert deck.swap_keys("key_1", "key_7")

    assert deck.key_order == (
        "key_7",
        "key_2",
        "key_3",
        "key_4",
        "key_5",
        "key_6",
        "key_1",
    )
    assert spy.count() == 1
    encoder_index = deck._grid.indexOf(deck._cards["encoder"])
    assert deck._grid.getItemPosition(encoder_index)[:2] == (0, 3)
    assert not deck.swap_keys("key_1", "encoder")


def test_key_card_drop_requests_swap_in_reorder_mode(qtbot, tmp_path) -> None:
    profile = default_gui_configuration(tmp_path).active_profile
    deck = DeckWidget(profile)
    qtbot.addWidget(deck)
    target = deck._cards["key_2"]
    spy = QSignalSpy(target.swap_requested)
    mime = QMimeData()
    mime.setData(CONTROL_MIME_TYPE, QByteArray(b"key_1"))
    event = QDropEvent(
        QPointF(5, 5),
        Qt.DropAction.MoveAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    deck.set_reorder_enabled(True)
    target.dropEvent(event)

    assert spy.count() == 1
    assert spy.at(0) == ["key_1", "key_2"]


def test_main_window_persists_global_key_order_without_updating_runtime(
    qtbot, tmp_path
) -> None:
    configuration = default_gui_configuration(tmp_path)
    repository = ConfigurationRepository(tmp_path / "config.json")
    repository.save(configuration, create_backup=False)
    runtime = FakeRuntime()
    window = MainWindow(configuration, repository, runtime)
    qtbot.addWidget(window)

    window.reorder_button.setChecked(True)
    assert window.deck.swap_keys("key_2", "key_6")

    saved = repository.load()
    assert saved.key_order == (
        "key_1",
        "key_6",
        "key_3",
        "key_4",
        "key_5",
        "key_2",
        "key_7",
    )
    assert window.configuration.key_order == saved.key_order
    assert runtime.applied == []

    window._duplicate_profile()
    assert window.deck.key_order == saved.key_order


def test_main_window_restores_key_order_when_save_fails(
    qtbot, tmp_path, monkeypatch
) -> None:
    configuration = default_gui_configuration(tmp_path)
    repository = ConfigurationRepository(tmp_path / "config.json")
    repository.save(configuration, create_backup=False)
    runtime = FakeRuntime()
    window = MainWindow(configuration, repository, runtime)
    qtbot.addWidget(window)
    errors = []

    def fail_save(updated) -> None:
        raise OSError("disco indisponível")

    monkeypatch.setattr(repository, "save", fail_save)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda parent, title, message: errors.append((title, message)),
    )

    window.reorder_button.setChecked(True)
    assert window.deck.swap_keys("key_1", "key_7")

    assert window.deck.key_order == configuration.key_order
    assert window.configuration.key_order == configuration.key_order
    assert errors == [("Erro ao salvar", "disco indisponível")]


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
