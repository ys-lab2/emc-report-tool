from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.countermeasure import Countermeasure
from repositories import countermeasure_repository
from services.project_service import ProjectHandle

DESCRIPTION_MIN_HEIGHT = 140


class CountermeasureCard(QFrame):
    def __init__(self, conn, item: Countermeasure, on_delete) -> None:
        super().__init__()
        self._conn = conn
        self._item = item
        self._on_delete = on_delete
        self._loading = False

        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.description_edit = QTextEdit(item.description)
        self.description_edit.setPlaceholderText(
            "EMC合格のために行った対策をできるだけ詳しく箇条書きで記入してください。"
        )
        self.description_edit.setMinimumHeight(DESCRIPTION_MIN_HEIGHT)

        self.model_edit = QLineEdit(item.component_model)
        self.manufacturer_edit = QLineEdit(item.component_manufacturer)

        delete_button = QPushButton("この対策を削除")
        delete_button.clicked.connect(lambda: self._on_delete(self))

        form = QFormLayout()
        form.addRow("対策部品のモデル名（必須）", self.model_edit)
        form.addRow("対策部品のメーカー名（必須）", self.manufacturer_edit)

        header_row = QHBoxLayout()
        header_row.addLayout(form)
        header_row.addWidget(delete_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_row)
        layout.addWidget(self.description_edit)

        self.model_edit.editingFinished.connect(self._save)
        self.manufacturer_edit.editingFinished.connect(self._save)
        self.description_edit.textChanged.connect(self._save)

    def _save(self) -> None:
        if self._loading:
            return
        self._item.description = self.description_edit.toPlainText()
        self._item.component_model = self.model_edit.text()
        self._item.component_manufacturer = self.manufacturer_edit.text()
        countermeasure_repository.update(self._conn, self._item)

    @property
    def item_id(self) -> str:
        return self._item.countermeasure_id


class CountermeasurePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._cards: list[CountermeasureCard] = []

        add_button = QPushButton("+ 対策を追加")
        add_button.clicked.connect(self._add_item)

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

        items = countermeasure_repository.list_by_project(self._handle.connection, self._handle.project.project_id)
        for item in items:
            self._add_card(item)

    def _add_card(self, item: Countermeasure) -> None:
        card = CountermeasureCard(self._handle.connection, item, self._remove_card)
        self._cards.append(card)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _add_item(self) -> None:
        if self._handle is None:
            return
        item = countermeasure_repository.add(
            self._handle.connection,
            Countermeasure(
                countermeasure_id="",
                project_id=self._handle.project.project_id,
                sort_order=len(self._cards),
            ),
        )
        self._add_card(item)

    def _remove_card(self, card: CountermeasureCard) -> None:
        countermeasure_repository.delete(self._handle.connection, card.item_id)
        self._cards.remove(card)
        card.setParent(None)
