from __future__ import annotations

from uuid import uuid4

from PySide6.QtTest import QSignalSpy

from streamdeck_monitor.application.defaults import default_gui_configuration
from streamdeck_monitor.gui.settings_dialog import SettingsDialog
from streamdeck_monitor.gui.single_instance import SingleInstance
from streamdeck_monitor.infrastructure.windows_startup import startup_command


def test_settings_dialog_builds_updated_configuration(qtbot, tmp_path) -> None:
    configuration = default_gui_configuration(tmp_path)
    dialog = SettingsDialog(configuration)
    qtbot.addWidget(dialog)

    dialog.port_edit.setText("COM7")
    dialog.scan_interval.setValue(1.5)
    dialog.startup_check.setChecked(True)
    dialog.event_limit.setValue(500)
    dialog.log_level.setCurrentText("DEBUG")
    result = dialog.result_configuration()

    assert result.serial.port == "COM7"
    assert result.serial.scan_interval_seconds == 1.5
    assert result.ui.start_with_windows
    assert result.ui.recent_event_limit == 500
    assert result.logging.level == "DEBUG"


def test_startup_command_reopens_gui_minimized() -> None:
    command = startup_command()
    assert "streamdeck_monitor.gui.bootstrap" in command
    assert "--minimized" in command


def test_single_instance_notifies_existing_process(qtbot) -> None:
    name = f"stream-deck-mini-test-{uuid4()}"
    primary = SingleInstance(name)
    secondary = SingleInstance(name)
    spy = QSignalSpy(primary.activation_requested)
    try:
        assert primary.acquire()
        assert not secondary.acquire()
        qtbot.waitUntil(lambda: spy.count() == 1, timeout=1000)
    finally:
        secondary.close()
        primary.close()
