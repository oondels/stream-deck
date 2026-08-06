from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from streamdeck_monitor.application.settings import GuiConfiguration, SerialSettings


class SettingsDialog(QDialog):
    def __init__(self, configuration: GuiConfiguration, parent=None) -> None:
        super().__init__(parent)
        self._configuration = configuration
        self.setWindowTitle("Configurações")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "Geral")
        tabs.addTab(self._device_tab(), "Dispositivo")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _general_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        self.startup_check = QCheckBox("Iniciar minimizado com o Windows")
        self.startup_check.setChecked(self._configuration.ui.start_with_windows)
        self.tray_check = QCheckBox("Minimizar para a bandeja ao fechar")
        self.tray_check.setChecked(self._configuration.ui.close_to_tray)
        self.event_limit = QSpinBox()
        self.event_limit.setRange(10, 10_000)
        self.event_limit.setValue(self._configuration.ui.recent_event_limit)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText(self._configuration.logging.level.upper())
        form.addRow(self.startup_check)
        form.addRow(self.tray_check)
        form.addRow("Eventos mantidos", self.event_limit)
        form.addRow("Nível de log", self.log_level)
        return tab

    def _device_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        self.port_edit = QLineEdit(self._configuration.serial.port or "auto")
        self.port_edit.setPlaceholderText("auto ou COM4")
        self.scan_interval = QDoubleSpinBox()
        self.scan_interval.setRange(0.2, 60.0)
        self.scan_interval.setDecimals(1)
        self.scan_interval.setSuffix(" s")
        self.scan_interval.setValue(self._configuration.serial.scan_interval_seconds)
        self.handshake_timeout = QDoubleSpinBox()
        self.handshake_timeout.setRange(0.5, 30.0)
        self.handshake_timeout.setDecimals(1)
        self.handshake_timeout.setSuffix(" s")
        self.handshake_timeout.setValue(
            self._configuration.serial.handshake_timeout_seconds
        )
        form.addRow("Porta serial", self.port_edit)
        form.addRow("Intervalo de busca", self.scan_interval)
        form.addRow("Tempo de handshake", self.handshake_timeout)
        return tab

    def result_configuration(self) -> GuiConfiguration:
        port = self.port_edit.text().strip()
        serial = SerialSettings(
            port=None if not port or port.casefold() == "auto" else port,
            baud_rate=115200,
            scan_interval_seconds=self.scan_interval.value(),
            handshake_timeout_seconds=self.handshake_timeout.value(),
        )
        ui = replace(
            self._configuration.ui,
            start_with_windows=self.startup_check.isChecked(),
            close_to_tray=self.tray_check.isChecked(),
            recent_event_limit=self.event_limit.value(),
        )
        logging = replace(
            self._configuration.logging, level=self.log_level.currentText()
        )
        return replace(self._configuration, serial=serial, ui=ui, logging=logging)
