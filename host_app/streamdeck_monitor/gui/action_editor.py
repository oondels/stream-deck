from __future__ import annotations

from dataclasses import replace
import shlex
from urllib.parse import urlparse

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from streamdeck_monitor.domain.actions import (
    Binding,
    HotkeyAction,
    LaunchAction,
    MediaAction,
    OpenUrlAction,
)
from streamdeck_monitor.domain.profiles import ControlAppearance, Profile
from streamdeck_monitor.infrastructure.configuration import ALLOWED_KEYS
from streamdeck_monitor.infrastructure.profile_configuration import ICONS

ACTION_TYPES = {
    "none": "Nenhuma",
    "media": "Mídia / volume",
    "hotkey": "Atalho de teclado",
    "launch": "Abrir aplicativo",
    "open_url": "Abrir URL",
}
MEDIA_COMMANDS = {
    "play_pause": "Reproduzir / pausar",
    "previous_track": "Faixa anterior",
    "next_track": "Próxima faixa",
    "stop": "Parar",
    "volume_up": "Aumentar volume",
    "volume_down": "Diminuir volume",
    "volume_mute": "Silenciar volume",
}
ICON_LABELS = {
    "none": "Nenhum",
    "previous": "Anterior",
    "play": "Reproduzir",
    "next": "Próxima",
    "stop": "Parar",
    "desktop": "Área de trabalho",
    "calculator": "Calculadora",
    "globe": "Internet",
    "volume": "Volume",
    "mute": "Silenciar",
    "keyboard": "Teclado",
    "application": "Aplicativo",
}


class ActionEditor(QFrame):
    profile_changed = Signal(object)
    test_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._profile: Profile | None = None
        self._control = "key_1"
        self._loading = False

        root = QVBoxLayout(self)
        title = QLabel("Configurar controle")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        form = QFormLayout()
        self.label_edit = QLineEdit()
        self.icon_combo = QComboBox()
        for icon in sorted(ICONS):
            self.icon_combo.addItem(ICON_LABELS.get(icon, icon), icon)
        self.color_button = QPushButton("Escolher cor")
        self.trigger_combo = QComboBox()
        self.action_combo = QComboBox()
        for action_type, label in ACTION_TYPES.items():
            self.action_combo.addItem(label, action_type)
        self.media_combo = QComboBox()
        for command, label in MEDIA_COMMANDS.items():
            self.media_combo.addItem(label, command)
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("Ctrl+Alt+K")
        self.executable_edit = QLineEdit()
        self.executable_edit.setPlaceholderText(r"C:\Program Files\Aplicativo\app.exe")
        self.arguments_edit = QLineEdit()
        self.arguments_edit.setPlaceholderText('--opcao "valor"')
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://exemplo.com")

        form.addRow("Nome", self.label_edit)
        form.addRow("Ícone", self.icon_combo)
        form.addRow("Cor", self.color_button)
        form.addRow("Evento", self.trigger_combo)
        form.addRow("Ação", self.action_combo)
        form.addRow("Comando", self.media_combo)
        form.addRow("Teclas", self.hotkey_edit)
        form.addRow("Executável", self.executable_edit)
        form.addRow("Argumentos", self.arguments_edit)
        form.addRow("URL", self.url_edit)
        self._form = form
        root.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)

        buttons = QHBoxLayout()
        self.test_button = QPushButton("Testar ação")
        self.test_button.setObjectName("primary")
        buttons.addStretch()
        buttons.addWidget(self.test_button)
        root.addLayout(buttons)
        root.addStretch()

        self.label_edit.editingFinished.connect(self._save)
        self.icon_combo.currentIndexChanged.connect(self._save)
        self.color_button.clicked.connect(self._choose_color)
        self.trigger_combo.currentIndexChanged.connect(self._load_binding)
        self.action_combo.currentIndexChanged.connect(self._action_type_changed)
        self.media_combo.currentIndexChanged.connect(self._save)
        self.hotkey_edit.editingFinished.connect(self._save)
        self.executable_edit.editingFinished.connect(self._save)
        self.arguments_edit.editingFinished.connect(self._save)
        self.url_edit.editingFinished.connect(self._save)
        self.test_button.clicked.connect(self._test)

    def set_control(self, profile: Profile, control: str) -> None:
        self._profile = profile
        self._control = control
        self._loading = True
        appearance = next(item for item in profile.display if item.control == control)
        self.label_edit.setText(appearance.label)
        self.icon_combo.setCurrentIndex(self.icon_combo.findData(appearance.icon))
        self._set_color(appearance.color)
        self.trigger_combo.clear()
        if control == "encoder":
            self.trigger_combo.addItem(
                "Girar no sentido horário", ("encoder_cw", "rotate")
            )
            self.trigger_combo.addItem(
                "Girar no sentido anti-horário", ("encoder_ccw", "rotate")
            )
            self.trigger_combo.addItem("Pressionar", ("encoder_press", "press"))
            self.trigger_combo.addItem("Soltar", ("encoder_press", "release"))
        else:
            self.trigger_combo.addItem("Pressionar", (control, "press"))
            self.trigger_combo.addItem("Soltar", (control, "release"))
        self._loading = False
        self._load_binding()

    def _load_binding(self) -> None:
        if self._loading or self._profile is None:
            return
        self._loading = True
        binding = self._current_binding()
        action_type = binding.action.type if binding else "none"
        self.action_combo.setCurrentIndex(self.action_combo.findData(action_type))
        self.media_combo.setCurrentIndex(0)
        self.hotkey_edit.clear()
        self.executable_edit.clear()
        self.arguments_edit.clear()
        self.url_edit.clear()
        if binding and isinstance(binding.action, MediaAction):
            self.media_combo.setCurrentIndex(
                self.media_combo.findData(binding.action.command)
            )
        elif binding and isinstance(binding.action, HotkeyAction):
            self.hotkey_edit.setText("+".join(binding.action.keys))
        elif binding and isinstance(binding.action, LaunchAction):
            self.executable_edit.setText(binding.action.executable)
            self.arguments_edit.setText(
                " ".join(shlex.quote(argument) for argument in binding.action.args)
            )
        elif binding and isinstance(binding.action, OpenUrlAction):
            self.url_edit.setText(binding.action.url)
        self._loading = False
        self._update_action_fields()
        self.error_label.clear()

    def _action_type_changed(self) -> None:
        if self._loading:
            return
        self._update_action_fields()
        self._save()

    def _update_action_fields(self) -> None:
        selected = self.action_combo.currentData()
        self._set_field_visible(self.media_combo, selected == "media")
        self._set_field_visible(self.hotkey_edit, selected == "hotkey")
        self._set_field_visible(self.executable_edit, selected == "launch")
        self._set_field_visible(self.arguments_edit, selected == "launch")
        self._set_field_visible(self.url_edit, selected == "open_url")

    def _set_field_visible(self, field, visible: bool) -> None:
        field.setVisible(visible)
        label = self._form.labelForField(field)
        if label is not None:
            label.setVisible(visible)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(
            QColor(self.color_button.property("deckColor")), self
        )
        if color.isValid():
            self._set_color(color.name().upper())
            self._save()

    def _set_color(self, color: str) -> None:
        self.color_button.setProperty("deckColor", color)
        self.color_button.setText(color)
        self.color_button.setStyleSheet(f"background-color: {color};")

    def _save(self) -> None:
        if self._loading or self._profile is None:
            return
        try:
            profile = self._updated_profile()
        except ValueError as error:
            self.error_label.setText(str(error))
            return
        self.error_label.clear()
        self._profile = profile
        self.profile_changed.emit(profile)

    def _updated_profile(self) -> Profile:
        assert self._profile is not None
        label = self.label_edit.text().strip()
        if not label:
            raise ValueError("O nome do controle não pode ficar vazio.")
        appearance = ControlAppearance(
            self._control,
            label,
            str(self.icon_combo.currentData()),
            str(self.color_button.property("deckColor")),
        )
        display = tuple(
            appearance if item.control == self._control else item
            for item in self._profile.display
        )

        trigger_control, trigger_event = self.trigger_combo.currentData()
        current = self._current_binding()
        bindings = tuple(
            item
            for item in self._profile.bindings
            if (item.control, item.event) != (trigger_control, trigger_event)
        )
        action_type = self.action_combo.currentData()
        if action_type == "none":
            return replace(self._profile, display=display, bindings=bindings)
        action = self._build_action(str(action_type))
        binding_id = current.id if current else f"{trigger_control}-{trigger_event}"
        return replace(
            self._profile,
            display=display,
            bindings=(
                *bindings,
                Binding(binding_id, trigger_control, trigger_event, action),
            ),
        )

    def _build_action(self, action_type: str):
        if action_type == "media":
            return MediaAction(str(self.media_combo.currentData()))
        if action_type == "hotkey":
            keys = tuple(
                part.strip().lower()
                for part in self.hotkey_edit.text().split("+")
                if part.strip()
            )
            if not keys:
                raise ValueError("Informe ao menos uma tecla para o atalho.")
            unknown = set(keys) - ALLOWED_KEYS
            if unknown:
                raise ValueError(
                    f"Teclas não suportadas: {', '.join(sorted(unknown))}."
                )
            if len(keys) != len(set(keys)):
                raise ValueError("O atalho não pode repetir teclas.")
            return HotkeyAction(keys)
        if action_type == "launch":
            executable = self.executable_edit.text().strip()
            if not executable:
                raise ValueError("Informe o executável do aplicativo.")
            try:
                arguments = tuple(shlex.split(self.arguments_edit.text(), posix=False))
            except ValueError as error:
                raise ValueError(f"Argumentos inválidos: {error}.") from error
            return LaunchAction(executable, arguments)
        if action_type == "open_url":
            url = self.url_edit.text().strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Informe uma URL HTTP(S) válida.")
            return OpenUrlAction(url)
        raise ValueError("Tipo de ação inválido.")

    def _current_binding(self) -> Binding | None:
        if self._profile is None or self.trigger_combo.currentData() is None:
            return None
        control, event = self.trigger_combo.currentData()
        return next(
            (
                item
                for item in self._profile.bindings
                if (item.control, item.event) == (control, event)
            ),
            None,
        )

    def _test(self) -> None:
        binding = self._current_binding()
        if binding is None:
            self.error_label.setText("Este evento não possui uma ação para testar.")
            return
        self.test_requested.emit(binding.id)
