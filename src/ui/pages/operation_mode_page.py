from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.operation_mode import OperationMode
from repositories import operation_mode_repository
from services.project_service import ProjectHandle

DESCRIPTION_MIN_HEIGHT = 160


class OperationModeCard(QFrame):
    def __init__(self, conn, mode: OperationMode, on_delete) -> None:
        super().__init__()
        self._conn = conn
        self._mode = mode
        self._on_delete = on_delete
        self._loading = False

        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.name_edit = QLineEdit(mode.mode_name)
        self.name_edit.setPlaceholderText("モード名（例：通常動作モード）")
        delete_button = QPushButton("このモードを削除")
        delete_button.clicked.connect(lambda: self._on_delete(self))

        self.description_edit = QTextEdit(mode.description)
        self.description_edit.setPlaceholderText("動作の説明を自由に記入してください（各ポートごとの動作内容も含めて可）。")
        self.description_edit.setMinimumHeight(DESCRIPTION_MIN_HEIGHT)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("モード名"))
        header_row.addWidget(self.name_edit)
        header_row.addWidget(delete_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_row)
        layout.addWidget(self.description_edit)

        self.name_edit.editingFinished.connect(self._save)
        self.description_edit.textChanged.connect(self._save)

    def _save(self) -> None:
        if self._loading:
            return
        self._mode.mode_name = self.name_edit.text()
        self._mode.description = self.description_edit.toPlainText()
        operation_mode_repository.update(self._conn, self._mode)

    @property
    def mode_id(self) -> str:
        return self._mode.operation_mode_id


class OperationModePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._cards: list[OperationModeCard] = []

        add_button = QPushButton("+ 動作モードを追加")
        add_button.clicked.connect(self._add_mode)

        self.cards_layout = QVBoxLayout()
        self.cards_layout.addStretch(1)

        cards_container = QWidget()
        cards_container.setLayout(self.cards_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cards_container)

        layout = QVBoxLayout(self)
        layout.addWidget(add_button)
        layout.addWidget(scroll)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return

        for card in self._cards:
            card.setParent(None)
        self._cards.clear()

        modes = operation_mode_repository.list_by_project(self._handle.connection, self._handle.project.project_id)
        for mode in modes:
            self._add_card(mode)

    def _add_card(self, mode: OperationMode) -> None:
        card = OperationModeCard(self._handle.connection, mode, self._remove_card)
        self._cards.append(card)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _add_mode(self) -> None:
        if self._handle is None:
            return
        mode = operation_mode_repository.add(
            self._handle.connection,
            OperationMode(
                operation_mode_id="",
                project_id=self._handle.project.project_id,
                sort_order=len(self._cards),
            ),
        )
        self._add_card(mode)

    def _remove_card(self, card: OperationModeCard) -> None:
        operation_mode_repository.delete(self._handle.connection, card.mode_id)
        self._cards.remove(card)
        card.setParent(None)
