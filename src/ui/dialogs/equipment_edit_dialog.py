from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from models.equipment import CATEGORIES, Equipment
from repositories import equipment_repository
from services import equipment_service
from services.equipment_service import CircularContainmentError

CATEGORY_LABELS = {
    "EUT": "EUT",
    "Peripheral": "Peripheral",
    "AssociatedEquipment": "Associated Equipment",
    "Other": "Other",
}


class EquipmentEditDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, project_id: str, equipment: Equipment | None, parent=None) -> None:
        super().__init__(parent)
        self._conn = conn
        self._project_id = project_id
        self._is_new = equipment is None
        self._equipment = equipment or Equipment(
            equipment_id="",
            project_id=project_id,
            display_id=equipment_service.next_display_id(conn, project_id),
        )

        self.setWindowTitle("機器編集" if not self._is_new else "機器を新規追加")
        self.resize(480, 560)

        self.display_id_edit = QLineEdit(self._equipment.display_id)

        self.category_group = QButtonGroup(self)
        self.category_radios: dict[str, QRadioButton] = {}
        category_row = QHBoxLayout()
        for code in CATEGORIES:
            radio = QRadioButton(CATEGORY_LABELS[code])
            self.category_radios[code] = radio
            self.category_group.addButton(radio)
            category_row.addWidget(radio)
        self.category_radios[self._equipment.category].setChecked(True)

        self.description_edit = QLineEdit(self._equipment.description)
        self.model_name_edit = QLineEdit(self._equipment.model_name)
        self.serial_edit = QLineEdit(self._equipment.serial)
        self.manufacturer_edit = QLineEdit(self._equipment.manufacturer)
        self.fcc_id_edit = QLineEdit(self._equipment.fcc_id)
        self.bsmi_id_edit = QLineEdit(self._equipment.bsmi_id)
        self.notes_edit = QTextEdit(self._equipment.notes)
        self.notes_edit.setFixedHeight(80)

        self.width_edit = QLineEdit(_format_dimension(self._equipment.width_mm))
        self.depth_edit = QLineEdit(_format_dimension(self._equipment.depth_mm))
        self.height_edit = QLineEdit(_format_dimension(self._equipment.height_mm))

        self.placement_standalone_radio = QRadioButton("独立機器")
        self.placement_embedded_radio = QRadioButton("他機器に内蔵・挿入")
        self.placement_attached_radio = QRadioButton("外付け取付")
        self.placement_group = QButtonGroup(self)
        for radio in (
            self.placement_standalone_radio,
            self.placement_embedded_radio,
            self.placement_attached_radio,
        ):
            self.placement_group.addButton(radio)

        self.parent_combo = QComboBox()
        self._populate_parent_combo()

        placement = self._equipment.placement_type
        if placement in ("embedded", "inserted"):
            self.placement_embedded_radio.setChecked(True)
        elif placement == "attached":
            self.placement_attached_radio.setChecked(True)
        else:
            self.placement_standalone_radio.setChecked(True)
        self._sync_parent_combo_enabled()

        self.placement_standalone_radio.toggled.connect(self._sync_parent_combo_enabled)
        self.placement_embedded_radio.toggled.connect(self._sync_parent_combo_enabled)
        self.placement_attached_radio.toggled.connect(self._sync_parent_combo_enabled)

        form = QFormLayout()
        form.addRow("表示ID", self.display_id_edit)
        form.addRow("カテゴリ", category_row)
        form.addRow("機器名(Description)", self.description_edit)
        form.addRow("モデル名", self.model_name_edit)
        form.addRow("シリアル番号", self.serial_edit)
        form.addRow("製造者", self.manufacturer_edit)
        form.addRow("FCC ID", self.fcc_id_edit)
        form.addRow("BSMI ID", self.bsmi_id_edit)

        dimension_row = QHBoxLayout()
        dimension_row.addWidget(QLabel("W"))
        dimension_row.addWidget(self.width_edit)
        dimension_row.addWidget(QLabel("D"))
        dimension_row.addWidget(self.depth_edit)
        dimension_row.addWidget(QLabel("H"))
        dimension_row.addWidget(self.height_edit)
        dimension_row.addWidget(QLabel("mm"))
        form.addRow("寸法(EUTの場合)", dimension_row)

        form.addRow("備考", self.notes_edit)

        placement_row = QVBoxLayout()
        placement_row.addWidget(self.placement_standalone_radio)
        placement_row.addWidget(self.placement_embedded_radio)
        placement_row.addWidget(self.placement_attached_radio)
        form.addRow("配置方法", placement_row)
        form.addRow("親機器", self.parent_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _populate_parent_combo(self) -> None:
        self.parent_combo.clear()
        self.parent_combo.addItem("（なし）", None)
        ineligible = equipment_service.get_ineligible_parent_ids(
            self._conn, self._equipment.equipment_id or None
        )
        for candidate in equipment_repository.list_by_project(self._conn, self._project_id):
            if candidate.equipment_id in ineligible:
                continue
            label = f"{candidate.display_id} : {candidate.description or candidate.model_name}"
            self.parent_combo.addItem(label, candidate.equipment_id)

        if self._equipment.parent_equipment_id:
            index = self.parent_combo.findData(self._equipment.parent_equipment_id)
            if index >= 0:
                self.parent_combo.setCurrentIndex(index)

    def _sync_parent_combo_enabled(self) -> None:
        needs_parent = not self.placement_standalone_radio.isChecked()
        self.parent_combo.setEnabled(needs_parent)
        if not needs_parent:
            self.parent_combo.setCurrentIndex(0)

    def _selected_category(self) -> str:
        for code, radio in self.category_radios.items():
            if radio.isChecked():
                return code
        return "EUT"

    def _selected_placement(self) -> str:
        if self.placement_embedded_radio.isChecked():
            return "embedded"
        if self.placement_attached_radio.isChecked():
            return "attached"
        return "standalone"

    def _on_accept(self) -> None:
        self._equipment.display_id = self.display_id_edit.text().strip()
        self._equipment.category = self._selected_category()
        self._equipment.description = self.description_edit.text()
        self._equipment.model_name = self.model_name_edit.text()
        self._equipment.serial = self.serial_edit.text()
        self._equipment.manufacturer = self.manufacturer_edit.text()
        self._equipment.fcc_id = self.fcc_id_edit.text()
        self._equipment.bsmi_id = self.bsmi_id_edit.text()
        self._equipment.notes = self.notes_edit.toPlainText()
        self._equipment.width_mm = _parse_dimension(self.width_edit.text())
        self._equipment.depth_mm = _parse_dimension(self.depth_edit.text())
        self._equipment.height_mm = _parse_dimension(self.height_edit.text())
        self._equipment.placement_type = self._selected_placement()
        self._equipment.parent_equipment_id = (
            self.parent_combo.currentData() if self.parent_combo.isEnabled() else None
        )

        try:
            if self._is_new:
                equipment_service.create_equipment(self._conn, self._equipment)
            else:
                equipment_service.update_equipment(self._conn, self._equipment)
        except CircularContainmentError as exc:
            QMessageBox.warning(self, "設定できません", str(exc))
            return

        self.accept()

    @property
    def equipment(self) -> Equipment:
        return self._equipment


def _format_dimension(value: float | None) -> str:
    if value is None:
        return ""
    if value == int(value):
        return str(int(value))
    return str(value)


def _parse_dimension(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
