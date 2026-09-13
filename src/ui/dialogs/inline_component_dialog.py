from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from models.inline_component import INLINE_COMPONENT_TYPES, POSITIONS, InlineComponent
from services import inline_component_service

COLUMNS = ["種類", "名称", "型式", "製造者", "数量", "位置", "備考"]


class InlineComponentDialog(QDialog):
    """ケーブル上のフェライトコア等のInlineComponentを管理するダイアログ（21.節）。"""

    def __init__(self, conn: sqlite3.Connection, cable_id: str, cable_label: str, parent=None) -> None:
        super().__init__(parent)
        self._conn = conn
        self._cable_id = cable_id
        self.setWindowTitle(f"ケーブル上の部品 - {cable_label}")
        self.resize(640, 360)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self._on_item_changed)

        add_button = QPushButton("+ 追加")
        delete_button = QPushButton("削除")
        add_button.clicked.connect(self._add_component)
        delete_button.clicked.connect(self._delete_selected)

        toolbar = QHBoxLayout()
        toolbar.addWidget(add_button)
        toolbar.addWidget(delete_button)
        toolbar.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        layout.addWidget(buttons)

        self._loading = False
        self.refresh()

    def refresh(self) -> None:
        self._loading = True
        self.table.setRowCount(0)
        components = inline_component_service.list_for_cable(self._conn, self._cable_id)
        for component in components:
            self._append_row(component)
        self._loading = False

    def _append_row(self, component: InlineComponent) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        type_combo = QComboBox()
        type_combo.addItems(INLINE_COMPONENT_TYPES)
        type_combo.setCurrentText(component.type)
        type_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 0, type_combo)

        name_item = QTableWidgetItem(component.name)
        name_item.setData(1000, component.inline_component_id)
        self.table.setItem(row, 1, name_item)
        self.table.setItem(row, 2, QTableWidgetItem(component.model))
        self.table.setItem(row, 3, QTableWidgetItem(component.manufacturer))

        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 999)
        quantity_spin.setValue(component.quantity)
        quantity_spin.valueChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 4, quantity_spin)

        position_combo = QComboBox()
        position_combo.addItems(POSITIONS)
        position_combo.setCurrentText(component.position)
        position_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 5, position_combo)

        self.table.setItem(row, 6, QTableWidgetItem(component.notes))

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        self._save_row(item.row())

    def _save_row(self, row: int) -> None:
        if self._loading:
            return
        name_item = self.table.item(row, 1)
        if name_item is None:
            return
        component_id = name_item.data(1000)

        type_combo: QComboBox = self.table.cellWidget(row, 0)
        quantity_spin: QSpinBox = self.table.cellWidget(row, 4)
        position_combo: QComboBox = self.table.cellWidget(row, 5)

        component = InlineComponent(
            inline_component_id=component_id,
            cable_id=self._cable_id,
            type=type_combo.currentText(),
            name=self._text(row, 1),
            model=self._text(row, 2),
            manufacturer=self._text(row, 3),
            quantity=quantity_spin.value(),
            position=position_combo.currentText(),
            notes=self._text(row, 6),
        )
        inline_component_service.update_component(self._conn, component)

    def _text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text() if item else ""

    def _add_component(self) -> None:
        component = inline_component_service.add_component(
            self._conn, InlineComponent(inline_component_id="", cable_id=self._cable_id)
        )
        self._append_row(component)

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        name_item = self.table.item(row, 1)
        if name_item is None:
            return
        component_id = name_item.data(1000)
        inline_component_service.delete_component(self._conn, component_id)
        self.table.removeRow(row)
