from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, message: str) -> None:
        super().__init__()
        label = QLabel(message)
        label.setContentsMargins(16, 16, 16, 16)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addStretch(1)

    def set_project(self, handle) -> None:  # noqa: ANN001 - 未実装ページはプロジェクトを使わない
        pass

    def refresh(self) -> None:
        pass
