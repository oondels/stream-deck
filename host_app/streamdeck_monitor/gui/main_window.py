from __future__ import annotations

from dataclasses import replace
import json
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from streamdeck_monitor.application.defaults import default_profile
from streamdeck_monitor.application.runtime_service import RuntimeService
from streamdeck_monitor.application.settings import GuiConfiguration
from streamdeck_monitor.domain.profiles import Profile
from streamdeck_monitor.gui.action_editor import ActionEditor
from streamdeck_monitor.gui.deck_widget import DeckWidget
from streamdeck_monitor.gui.runtime_bridge import RuntimeBridge
from streamdeck_monitor.infrastructure.config_repository import ConfigurationRepository
from streamdeck_monitor.infrastructure.event_sink import LogEntry


class MainWindow(QMainWindow):
    exit_requested = Signal()

    def __init__(
        self,
        configuration: GuiConfiguration,
        repository: ConfigurationRepository,
        runtime: RuntimeService,
    ) -> None:
        super().__init__()
        self.configuration = configuration
        self.repository = repository
        self.runtime = runtime
        self.bridge = RuntimeBridge(runtime)
        self._paused = False
        self._allow_close = False
        self.tray_enabled = False

        self.setWindowTitle("Stream Deck Mini")
        self.setMinimumSize(1040, 680)
        self.resize(1280, 780)
        self._build_ui()
        self._connect_runtime()
        self._load_profiles()
        self.statusBar().showMessage("Procurando dispositivo…")

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Stream Deck Mini")
        title.setObjectName("title")
        self.connection_label = QLabel("● Procurando dispositivo")
        self.connection_label.setObjectName("muted")
        self.pause_button = QPushButton("Pausar ações")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self._toggle_pause)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.connection_label)
        header.addWidget(self.pause_button)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_configuration_tab(), "Controles e perfis")
        self.tabs.addTab(self._build_events_tab(), "Eventos")
        root.addWidget(self.tabs)
        self.setCentralWidget(central)

        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.request_exit)
        file_menu = self.menuBar().addMenu("Arquivo")
        file_menu.addAction(exit_action)

    def _build_configuration_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        profile_panel = QFrame()
        profile_panel.setObjectName("panel")
        profile_layout = QVBoxLayout(profile_panel)
        heading = QLabel("Perfis")
        heading.setObjectName("sectionTitle")
        profile_layout.addWidget(heading)
        self.profile_list = QListWidget()
        self.profile_list.currentRowChanged.connect(self._activate_profile_row)
        profile_layout.addWidget(self.profile_list)
        create_button = QPushButton("Novo")
        duplicate_button = QPushButton("Duplicar")
        rename_button = QPushButton("Renomear")
        self.delete_profile_button = QPushButton("Excluir")
        self.delete_profile_button.setObjectName("danger")
        create_button.clicked.connect(self._create_profile)
        duplicate_button.clicked.connect(self._duplicate_profile)
        rename_button.clicked.connect(self._rename_profile)
        self.delete_profile_button.clicked.connect(self._delete_profile)
        profile_layout.addWidget(create_button)
        profile_layout.addWidget(duplicate_button)
        profile_layout.addWidget(rename_button)
        profile_layout.addWidget(self.delete_profile_button)

        deck_panel = QFrame()
        deck_panel.setObjectName("panel")
        deck_layout = QVBoxLayout(deck_panel)
        deck_heading = QLabel("Dispositivo")
        deck_heading.setObjectName("sectionTitle")
        deck_layout.addWidget(deck_heading)
        self.deck = DeckWidget(self.configuration.active_profile)
        self.deck.control_selected.connect(self._select_control)
        deck_layout.addWidget(self.deck)

        self.editor = ActionEditor()
        self.editor.profile_changed.connect(self._update_active_profile)
        self.editor.test_requested.connect(self._test_binding)

        splitter.addWidget(profile_panel)
        splitter.addWidget(deck_panel)
        splitter.addWidget(self.editor)
        splitter.setSizes([190, 610, 330])
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        return tab

    def _build_events_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        filters = QHBoxLayout()
        self.event_search = QLineEdit()
        self.event_search.setPlaceholderText("Filtrar eventos…")
        self.event_level = QComboBox()
        self.event_level.addItem("Todos os níveis", "")
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            self.event_level.addItem(level, level)
        self.event_search.textChanged.connect(self._filter_events)
        self.event_level.currentIndexChanged.connect(self._filter_events)
        filters.addWidget(self.event_search)
        filters.addWidget(self.event_level)
        layout.addLayout(filters)

        self.event_table = QTableWidget(0, 4)
        self.event_table.setHorizontalHeaderLabels(
            ["Horário", "Nível", "Evento", "Detalhes"]
        )
        self.event_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.event_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.event_table.verticalHeader().setVisible(False)
        self.event_table.horizontalHeader().setStretchLastSection(True)
        self.event_table.setColumnWidth(0, 105)
        self.event_table.setColumnWidth(1, 90)
        self.event_table.setColumnWidth(2, 170)
        layout.addWidget(self.event_table)
        return tab

    def _connect_runtime(self) -> None:
        self.bridge.connection_changed.connect(self._connection_changed)
        self.bridge.input_received.connect(self.deck.highlight_input)
        self.bridge.pause_changed.connect(self._set_paused)
        self.bridge.entry_received.connect(self._append_event)

    def _load_profiles(self) -> None:
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        active_row = 0
        for index, profile in enumerate(self.configuration.profiles):
            self.profile_list.addItem(profile.name)
            self.profile_list.item(index).setData(Qt.ItemDataRole.UserRole, profile.id)
            if profile.id == self.configuration.active_profile_id:
                active_row = index
        self.profile_list.setCurrentRow(active_row)
        self.profile_list.blockSignals(False)
        self.delete_profile_button.setEnabled(len(self.configuration.profiles) > 1)
        self._show_active_profile()

    def _show_active_profile(self) -> None:
        profile = self.configuration.active_profile
        self.deck.set_profile(profile)
        self.editor.set_control(profile, self.deck.selected_control)

    def _activate_profile_row(self, row: int) -> None:
        if row < 0:
            return
        profile_id = self.profile_list.item(row).data(Qt.ItemDataRole.UserRole)
        if profile_id == self.configuration.active_profile_id:
            return
        self.configuration = replace(self.configuration, active_profile_id=profile_id)
        self._persist_profile_change()
        self._show_active_profile()
        self.statusBar().showMessage(
            f"Perfil “{self.configuration.active_profile.name}” ativado", 3000
        )

    def _select_control(self, control: str) -> None:
        self.editor.set_control(self.configuration.active_profile, control)

    def _update_active_profile(self, profile: Profile) -> None:
        profiles = tuple(
            profile if item.id == profile.id else item
            for item in self.configuration.profiles
        )
        self.configuration = replace(self.configuration, profiles=profiles)
        self._persist_profile_change()
        self.deck.set_profile(profile)
        current = self.profile_list.currentItem()
        if current is not None:
            current.setText(profile.name)
        self.statusBar().showMessage("Alteração salva e aplicada", 2000)

    def _persist_profile_change(self) -> None:
        try:
            self.repository.save(self.configuration)
        except Exception as error:
            QMessageBox.critical(self, "Erro ao salvar", str(error))
            return
        self.runtime.apply_profile(self.configuration)

    def _create_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Novo perfil", "Nome do perfil:")
        if not accepted or not name.strip():
            return
        if self._profile_name_exists(name):
            QMessageBox.warning(
                self, "Nome em uso", "Já existe um perfil com esse nome."
            )
            return
        profile = default_profile(name=name.strip())
        self.configuration = replace(
            self.configuration,
            profiles=(*self.configuration.profiles, profile),
            active_profile_id=profile.id,
        )
        self._persist_profile_change()
        self._load_profiles()

    def _duplicate_profile(self) -> None:
        source = self.configuration.active_profile
        name = self._unique_profile_name(f"{source.name} - cópia")
        profile = replace(source, id=str(uuid4()), name=name)
        self.configuration = replace(
            self.configuration,
            profiles=(*self.configuration.profiles, profile),
            active_profile_id=profile.id,
        )
        self._persist_profile_change()
        self._load_profiles()

    def _rename_profile(self) -> None:
        current = self.configuration.active_profile
        name, accepted = QInputDialog.getText(
            self, "Renomear perfil", "Novo nome:", text=current.name
        )
        name = name.strip()
        if not accepted or not name or name == current.name:
            return
        if self._profile_name_exists(name):
            QMessageBox.warning(
                self, "Nome em uso", "Já existe um perfil com esse nome."
            )
            return
        self._update_active_profile(replace(current, name=name))

    def _delete_profile(self) -> None:
        if len(self.configuration.profiles) == 1:
            return
        profile = self.configuration.active_profile
        answer = QMessageBox.question(
            self,
            "Excluir perfil",
            f"Excluir o perfil “{profile.name}”?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        profiles = tuple(
            item for item in self.configuration.profiles if item.id != profile.id
        )
        self.configuration = replace(
            self.configuration, profiles=profiles, active_profile_id=profiles[0].id
        )
        self._persist_profile_change()
        self._load_profiles()

    def _profile_name_exists(self, name: str) -> bool:
        return any(
            item.name.casefold() == name.strip().casefold()
            for item in self.configuration.profiles
        )

    def _unique_profile_name(self, base: str) -> str:
        name = base
        suffix = 2
        while self._profile_name_exists(name):
            name = f"{base} ({suffix})"
            suffix += 1
        return name

    def _toggle_pause(self, paused: bool) -> None:
        if paused:
            self.runtime.pause_actions()
        else:
            self.runtime.resume_actions()
        self._set_paused(paused)

    def _set_paused(self, paused: bool) -> None:
        self._paused = paused
        self.pause_button.blockSignals(True)
        self.pause_button.setChecked(paused)
        self.pause_button.setText("Retomar ações" if paused else "Pausar ações")
        self.pause_button.blockSignals(False)

    def _test_binding(self, binding_id: str) -> None:
        if self.runtime.test_binding(binding_id):
            self.statusBar().showMessage("Ação enviada para teste", 2000)
        else:
            QMessageBox.warning(
                self, "Teste indisponível", "A ação não está disponível no runtime."
            )

    def _connection_changed(self, state: str, details: object) -> None:
        values = details if isinstance(details, dict) else {}
        if state == "connected":
            port = values.get("port", "")
            board = values.get("board", "")
            self.connection_label.setText(f"● Conectado — {port} ({board})")
            self.connection_label.setStyleSheet("color: #86EFAC;")
            self.statusBar().showMessage("Dispositivo conectado")
        elif state == "searching":
            self.connection_label.setText("● Procurando dispositivo")
            self.connection_label.setStyleSheet("color: #FDE68A;")
            self.statusBar().showMessage("Procurando dispositivo…")
        else:
            self.connection_label.setText("● Monitor parado")
            self.connection_label.setStyleSheet("color: #FCA5A5;")

    def _append_event(self, entry: LogEntry) -> None:
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        values = (
            entry.timestamp.astimezone().strftime("%H:%M:%S.%f")[:-3],
            entry.level,
            entry.event,
            json.dumps(entry.details, ensure_ascii=False, default=str),
        )
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.ItemDataRole.UserRole, entry.level)
            self.event_table.setItem(row, column, item)
        limit = self.configuration.ui.recent_event_limit
        while self.event_table.rowCount() > limit:
            self.event_table.removeRow(0)
        self._filter_events()
        self.event_table.scrollToBottom()

    def _filter_events(self) -> None:
        search = self.event_search.text().strip().casefold()
        level = str(self.event_level.currentData() or "")
        for row in range(self.event_table.rowCount()):
            row_level = self.event_table.item(row, 1).text()
            text = " ".join(
                self.event_table.item(row, column).text()
                for column in range(self.event_table.columnCount())
            ).casefold()
            self.event_table.setRowHidden(
                row,
                bool((level and row_level != level) or (search and search not in text)),
            )

    def request_exit(self) -> None:
        self._allow_close = True
        self.exit_requested.emit()
        self.close()

    def closeEvent(self, event) -> None:
        if (
            self._allow_close
            or not self.configuration.ui.close_to_tray
            or not self.tray_enabled
        ):
            event.accept()
        else:
            event.ignore()
            self.hide()

    def shutdown(self) -> None:
        self._allow_close = True
        self.bridge.close()
        self.runtime.stop()
