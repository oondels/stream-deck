from __future__ import annotations

from PySide6.QtCore import QByteArray, QMimeData, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from streamdeck_monitor.domain.profiles import (
    DEFAULT_KEY_ORDER,
    KEY_CONTROLS,
    ControlAppearance,
    Profile,
)

CONTROL_MIME_TYPE = "application/x-streamdeck-key-control"

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
    swap_requested = Signal(str, str)

    def __init__(self, appearance: ControlAppearance) -> None:
        super().__init__()
        self.control = appearance.control
        self._reorder_enabled = False
        self._drag_start = QPoint()
        self.setObjectName(f"card_{appearance.control}")
        self.setCheckable(True)
        self.setMinimumSize(128, 112)
        self.setAcceptDrops(True)
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
            "QPushButton[reordering=true] { border: 3px dashed #FDE047; }"
        )

    def set_reorder_enabled(self, enabled: bool) -> None:
        self._reorder_enabled = enabled and self.control in KEY_CONTROLS
        self.setProperty("reordering", self._reorder_enabled)
        self.setCursor(
            Qt.CursorShape.OpenHandCursor
            if self._reorder_enabled
            else Qt.CursorShape.ArrowCursor
        )
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._reorder_enabled and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._reorder_enabled or not (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            super().mouseMoveEvent(event)
            return
        distance = (event.position().toPoint() - self._drag_start).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        mime = QMimeData()
        mime.setData(CONTROL_MIME_TYPE, QByteArray(self.control.encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.position().toPoint())
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def dragEnterEvent(self, event) -> None:
        source = self._source_control(event.mimeData())
        if self._can_swap(source):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._can_swap(self._source_control(event.mimeData())):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        source = self._source_control(event.mimeData())
        if not self._can_swap(source):
            event.ignore()
            return
        self.swap_requested.emit(source, self.control)
        event.acceptProposedAction()

    def _can_swap(self, source: str) -> bool:
        return (
            self._reorder_enabled and source in KEY_CONTROLS and source != self.control
        )

    @staticmethod
    def _source_control(mime: QMimeData) -> str:
        if not mime.hasFormat(CONTROL_MIME_TYPE):
            return ""
        return bytes(mime.data(CONTROL_MIME_TYPE)).decode("utf-8", errors="ignore")

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
    key_order_changed = Signal(object)

    KEY_POSITIONS = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3))

    def __init__(
        self, profile: Profile, key_order: tuple[str, ...] = DEFAULT_KEY_ORDER
    ) -> None:
        super().__init__()
        self._cards: dict[str, ControlCard] = {}
        self._selected = "key_1"
        self._key_order = DEFAULT_KEY_ORDER
        self._reorder_enabled = False
        layout = QVBoxLayout(self)
        self._grid = QGridLayout()
        self._grid.setSpacing(14)
        layout.addStretch()
        layout.addLayout(self._grid)
        layout.addStretch()
        for appearance in profile.display:
            card = ControlCard(appearance)
            card.clicked.connect(
                lambda checked=False, control=appearance.control: self.select(control)
            )
            card.swap_requested.connect(self.swap_keys)
            self._cards[appearance.control] = card
        self._grid.addWidget(self._cards["encoder"], 0, 3)
        self.set_key_order(key_order)
        self.select(self._selected, emit=False)

    @property
    def selected_control(self) -> str:
        return self._selected

    @property
    def key_order(self) -> tuple[str, ...]:
        return self._key_order

    def set_profile(self, profile: Profile) -> None:
        for appearance in profile.display:
            self._cards[appearance.control].update_appearance(appearance)

    def set_key_order(self, key_order: tuple[str, ...]) -> None:
        if len(key_order) != len(KEY_CONTROLS) or set(key_order) != set(KEY_CONTROLS):
            raise ValueError("key_order must contain every key exactly once")
        self._key_order = tuple(key_order)
        for control, (row, column) in zip(self._key_order, self.KEY_POSITIONS):
            self._grid.addWidget(self._cards[control], row, column)

    def set_reorder_enabled(self, enabled: bool) -> None:
        self._reorder_enabled = enabled
        for control, card in self._cards.items():
            card.set_reorder_enabled(enabled and control in KEY_CONTROLS)

    def swap_keys(self, source: str, target: str) -> bool:
        if (
            not self._reorder_enabled
            or source not in KEY_CONTROLS
            or target not in KEY_CONTROLS
            or source == target
        ):
            return False
        order = list(self._key_order)
        source_index = order.index(source)
        target_index = order.index(target)
        order[source_index], order[target_index] = (
            order[target_index],
            order[source_index],
        )
        self.set_key_order(tuple(order))
        self.key_order_changed.emit(self._key_order)
        return True

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
