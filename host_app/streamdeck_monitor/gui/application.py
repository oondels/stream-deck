from __future__ import annotations

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
)

from streamdeck_monitor.application.runtime_service import RuntimeService
from streamdeck_monitor.gui.main_window import MainWindow
from streamdeck_monitor.gui.theme import DARK_STYLESHEET
from streamdeck_monitor.infrastructure.config_repository import ConfigurationRepository
from streamdeck_monitor.infrastructure.configuration import ConfigurationError


def run(minimized: bool = False) -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("Stream Deck Mini")
    application.setOrganizationName("StreamDeckMini")
    application.setStyleSheet(DARK_STYLESHEET)

    repository = ConfigurationRepository()
    try:
        configuration = repository.load_or_create()
    except ConfigurationError as error:
        QMessageBox.critical(
            None,
            "Configuração inválida",
            f"Não foi possível abrir a configuração:\n{error}",
        )
        return 2

    runtime = RuntimeService(configuration)
    window = MainWindow(configuration, repository, runtime)
    tray = _create_tray(application, window)
    window.tray_enabled = tray is not None

    shutting_down = False

    def shutdown() -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        window.shutdown()
        if tray is not None:
            tray.hide()
        application.quit()

    window.exit_requested.connect(shutdown)
    application.aboutToQuit.connect(window.shutdown)
    runtime.start()

    if not minimized or tray is None:
        window.show()
    elif tray is not None:
        tray.showMessage(
            "Stream Deck Mini",
            "O aplicativo está ativo na bandeja.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )
    return application.exec()


def _create_tray(
    application: QApplication, window: MainWindow
) -> QSystemTrayIcon | None:
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    application.setQuitOnLastWindowClosed(False)
    icon = application.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray = QSystemTrayIcon(icon, window)
    tray.setToolTip("Stream Deck Mini")
    menu = QMenu()
    open_action = QAction("Abrir", menu)
    pause_action = QAction("Pausar ações", menu)
    pause_action.setCheckable(True)
    profiles_menu = menu.addMenu("Perfil")
    menu.insertAction(profiles_menu.menuAction(), open_action)
    menu.insertSeparator(profiles_menu.menuAction())
    menu.addSeparator()
    exit_action = menu.addAction("Sair")

    def show_window() -> None:
        window.showNormal()
        window.raise_()
        window.activateWindow()

    def toggle_pause(paused: bool) -> None:
        window.pause_button.setChecked(paused)
        window.pause_button.clicked.emit(paused)

    def rebuild_profiles() -> None:
        profiles_menu.clear()
        for row, profile in enumerate(window.configuration.profiles):
            action = profiles_menu.addAction(profile.name)
            action.setCheckable(True)
            action.setChecked(profile.id == window.configuration.active_profile_id)
            action.triggered.connect(
                lambda checked=False, index=row: window.profile_list.setCurrentRow(
                    index
                )
            )

    open_action.triggered.connect(show_window)
    pause_action.triggered.connect(toggle_pause)
    profiles_menu.aboutToShow.connect(rebuild_profiles)
    exit_action.triggered.connect(window.request_exit)
    tray.activated.connect(
        lambda reason: (
            show_window()
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick
            else None
        )
    )
    tray.setContextMenu(menu)
    tray.show()
    return tray
