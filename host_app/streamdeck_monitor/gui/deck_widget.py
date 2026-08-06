from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget

from streamdeck_monitor.domain.profiles import ControlAppearance, Profile

ICON_GLYPHS = {
    "none": "•",
    "previous": "⏮",
    "play": "⏯",
    "next": "⏭",
    "stop": "⏹",
    "desktop": "▣",
    "calculator": "⌨",
    "globe": "◎",
    "volume": "◖",
    "mute": "⊘",
    "keyboard": "⌨",
    "application": "▤",
}


class ControlCard(QPushButton):
    def __init__(self, appearance: ControlAppearance) -> None:
        super().__init__()
        self.control = appearance.control
        self.setObjectName(f"card_{appearance.control}")
        self.setCheckable(True)
        self.setMinimumSize(128, 112)
        self.update_appearance(appearance)

    def update_appearance(self, appearance: ControlAppearance) -> None:
        self.setText(f"{ICON_GLYPHS.get(appearance.icon, '•')}\n{appearance.label}")
        self.setToolTip(appearance.control)
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {appearance.color};"
            "border: 2px solid rgba(255,255,255,35); border-radius: 12px;"
            "font-size: 12pt; font-weight: 600; padding: 10px;"
            "}"
            "QPushButton:hover { border-color: rgba(255,255,255,120); }"
            "QPushButton:checked { border: 3px solid #F8FAFC; }"
            "QPushButton[active=true] { border: 4px solid #FDE047; }"
        )

    def flash(self) -> None:
        self.setProperty("active", True)
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(180, self._clear_flash)

    def _clear_flash(self) -> None:
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)


class DeckWidget(QWidget):
    control_selected = Signal(str)

    POSITIONS = {
        "key_1": (0, 0),
        "key_2": (0, 1),
        "key_3": (0, 2),
        "encoder": (0, 3),
        "key_4": (1, 0),
        "key_5": (1, 1),
        "key_6": (1, 2),
        "key_7": (1, 3),
    }

    def __init__(self, profile: Profile) -> None:
        super().__init__()
        self._cards: dict[str, ControlCard] = {}
        self._selected = "key_1"
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setSpacing(14)
        layout.addStretch()
        layout.addLayout(grid)
        layout.addStretch()
        for appearance in profile.display:
            card = ControlCard(appearance)
            card.clicked.connect(
                lambda checked=False, control=appearance.control: self.select(control)
            )
            row, column = self.POSITIONS[appearance.control]
            grid.addWidget(card, row, column)
            self._cards[appearance.control] = card
        self.select(self._selected, emit=False)

    @property
    def selected_control(self) -> str:
        return self._selected

    def set_profile(self, profile: Profile) -> None:
        for appearance in profile.display:
            self._cards[appearance.control].update_appearance(appearance)

    def select(self, control: str, emit: bool = True) -> None:
        if control not in self._cards:
            return
        self._selected = control
        for name, card in self._cards.items():
            card.setChecked(name == control)
        if emit:
            self.control_selected.emit(control)

    def highlight_input(self, control: str, event: str) -> None:
        del event
        physical = "encoder" if control.startswith("encoder_") else control
        card = self._cards.get(physical)
        if card is not None:
            card.flash()
