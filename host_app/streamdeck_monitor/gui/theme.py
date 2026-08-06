DARK_STYLESHEET = """
QWidget {
    background: #111827;
    color: #E5E7EB;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow, QDialog { background: #0B1120; }
QFrame#panel {
    background: #172033;
    border: 1px solid #293449;
    border-radius: 10px;
}
QLabel#title { font-size: 18pt; font-weight: 600; }
QLabel#sectionTitle { font-size: 12pt; font-weight: 600; }
QLabel#muted { color: #94A3B8; }
QLabel#error { color: #FCA5A5; }
QPushButton {
    background: #263247;
    border: 1px solid #3B4961;
    border-radius: 6px;
    padding: 7px 12px;
}
QPushButton:hover { background: #334155; }
QPushButton:pressed { background: #1E293B; }
QPushButton:checked { background: #2563EB; border-color: #60A5FA; }
QPushButton#primary { background: #2563EB; border-color: #3B82F6; }
QPushButton#danger { color: #FCA5A5; }
QLineEdit, QComboBox, QSpinBox, QListWidget, QTableWidget {
    background: #0F172A;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 6px;
    selection-background-color: #2563EB;
}
QListWidget::item { padding: 8px; border-radius: 4px; }
QListWidget::item:selected { background: #2563EB; }
QHeaderView::section {
    background: #172033;
    color: #CBD5E1;
    padding: 6px;
    border: 0;
    border-bottom: 1px solid #334155;
}
QSplitter::handle { background: #263247; width: 1px; }
QStatusBar { background: #0F172A; color: #94A3B8; }
"""
