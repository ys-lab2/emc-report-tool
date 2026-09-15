from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.cable import Cable
from repositories import cable_repository, equipment_repository, ground_connection_repository, power_source_repository
from services import cable_service
from services.project_service import ProjectHandle
from ui.dialogs.inline_component_dialog import InlineComponentDialog

SHIELDED_OPTIONS = [("unknown", "未設定"), ("shielded", "Shielded"), ("non_shielded", "Non-shielded")]
OUTDOOR_OPTIONS = [("unknown", "未設定"), ("yes", "する"), ("no", "しない")]

CABLE_ID_ROLE = Qt.UserRole

COLUMNS = [
    "No.",
    "From",
    "From Port",
    "To",
    "To Port",
    "Cable Type",
    "Length(m)",
    "Shielded",
    "製造者仕様上限長さ",
    "屋外直接接続",
    "備考",
]


def _connectable_nodes(conn, project_id: str) -> list[tuple[str, str, str, str]]:
    """(ref_type, ref_id, label)のタプル一覧。ケーブルはEquipmentだけでなく
    PowerSource(電源)・GroundConnection(GND/PE)にも接続できる。"""
    nodes: list[tuple[str, str, str, str]] = []
    for eq in equipment_repository.list_by_project(conn, project_id):
        label = f"{eq.display_id} : {eq.description or eq.model_name}"
        nodes.append(("Equipment", eq.equipment_id, label))
    for power in power_source_repository.list_by_project(conn, project_id):
        label = f"[電源] {power.label or power.kind}"
        nodes.append(("PowerSource", power.power_source_id, label))
    for ground in ground_connection_repository.list_by_project(conn, project_id):
        label = f"[GND] {ground.label or ground.kind}"
        nodes.append(("GroundConnection", ground.ground_connection_id, label))
    return nodes


class CableListPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._loading = False

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)

        add_button = QPushButton("+ 新規ケーブル")
        delete_button = QPushButton("削除")
        add_button.clicked.connect(self._add_cable)
        delete_button.clicked.connect(self._delete_selected)

        toolbar = QHBoxLayout()
        toolbar.addWidget(add_button)
        toolbar.addWidget(delete_button)
        toolbar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        self.table.setRowCount(0)

        conn = self._handle.connection
        project_id = self._handle.project.project_id
        cables = cable_repository.list_by_project(conn, project_id)
        nodes = _connectable_nodes(conn, project_id)

        for cable in cables:
            self._append_row(cable, nodes)

        self._loading = False

    def _append_row(self, cable: Cable, nodes) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        no_item = QTableWidgetItem(str(cable.cable_no))
        no_item.setData(CABLE_ID_ROLE, cable.cable_id)
        self.table.setItem(row, 0, no_item)

        from_combo = self._make_node_combo(nodes, cable.from_ref_type, cable.from_ref_id)
        from_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 1, from_combo)

        self.table.setItem(row, 2, QTableWidgetItem(cable.from_port))

        to_combo = self._make_node_combo(nodes, cable.to_ref_type, cable.to_ref_id)
        to_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 3, to_combo)

        self.table.setItem(row, 4, QTableWidgetItem(cable.to_port))
        self.table.setItem(row, 5, QTableWidgetItem(cable.cable_type))
        self.table.setItem(row, 6, QTableWidgetItem("" if cable.length is None else str(cable.length)))

        shielded_combo = self._make_option_combo(SHIELDED_OPTIONS, cable.shielded)
        shielded_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 7, shielded_combo)

        self.table.setItem(row, 8, QTableWidgetItem(cable.maximum_length))

        outdoor_combo = self._make_option_combo(OUTDOOR_OPTIONS, cable.outdoor_connection)
        outdoor_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_row(r))
        self.table.setCellWidget(row, 9, outdoor_combo)

        self.table.setItem(row, 10, QTableWidgetItem(cable.notes))

    def _make_node_combo(self, nodes, selected_ref_type: str, selected_ref_id: str) -> QComboBox:
        combo = QComboBox()
        for ref_type, ref_id, label in nodes:
            combo.addItem(label, (ref_type, ref_id))
        for i in range(combo.count()):
            ref_type, ref_id = combo.itemData(i)
            if ref_type == selected_ref_type and ref_id == selected_ref_id:
                combo.setCurrentIndex(i)
                break
        return combo

    def _make_option_combo(self, options, selected_value: str) -> QComboBox:
        combo = QComboBox()
        for value, label in options:
            combo.addItem(label, value)
        index = combo.findData(selected_value)
        if index >= 0:
            combo.setCurrentIndex(index)
        return combo

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        self._save_row(item.row())

    def _save_row(self, row: int) -> None:
        if self._handle is None or self._loading:
            return

        no_item = self.table.item(row, 0)
        if no_item is None:
            return
        cable_id = no_item.data(CABLE_ID_ROLE)
        if not cable_id:
            return

        conn = self._handle.connection
        cable = cable_repository.get(conn, cable_id)
        if cable is None:
            return

        from_combo: QComboBox = self.table.cellWidget(row, 1)
        to_combo: QComboBox = self.table.cellWidget(row, 3)
        shielded_combo: QComboBox = self.table.cellWidget(row, 7)
        outdoor_combo: QComboBox = self.table.cellWidget(row, 9)

        cable.from_ref_type, cable.from_ref_id = from_combo.currentData()
        cable.from_port = self._text(row, 2)
        cable.to_ref_type, cable.to_ref_id = to_combo.currentData()
        cable.to_port = self._text(row, 4)
        cable.cable_type = self._text(row, 5)
        cable.length = _parse_float(self._text(row, 6))
        cable.shielded = shielded_combo.currentData()
        cable.maximum_length = self._text(row, 8)
        cable.outdoor_connection = outdoor_combo.currentData()
        cable.notes = self._text(row, 10)

        try:
            cable_service.update_cable(conn, cable)
        except cable_service.InvalidEquipmentReferenceError as exc:
            QMessageBox.warning(self, "保存できません", str(exc))
            self.refresh()

    def _text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text() if item else ""

    def _add_cable(self) -> None:
        if self._handle is None:
            return
        conn = self._handle.connection
        project_id = self._handle.project.project_id
        nodes = _connectable_nodes(conn, project_id)
        if len(nodes) < 2:
            QMessageBox.information(
                self, "接続先が不足しています", "ケーブルを追加するには機器・電源・GNDが2つ以上必要です。"
            )
            return

        cable = Cable(
            cable_id="",
            project_id=project_id,
            from_ref_type=nodes[0][0],
            from_ref_id=nodes[0][1],
            to_ref_type=nodes[1][0],
            to_ref_id=nodes[1][1],
        )
        cable_service.create_cable(conn, cable)
        self.refresh()

    def _delete_selected(self) -> None:
        if self._handle is None:
            return
        row = self.table.currentRow()
        if row < 0:
            return
        no_item = self.table.item(row, 0)
        if no_item is None:
            return
        cable_id = no_item.data(CABLE_ID_ROLE)
        if not cable_id:
            return

        cable_service.delete_cable(self._handle.connection, cable_id)
        self.refresh()

    def _on_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row < 0 or self._handle is None:
            return
        no_item = self.table.item(row, 0)
        if no_item is None:
            return
        cable_id = no_item.data(CABLE_ID_ROLE)
        if not cable_id:
            return

        menu = QMenu(self)
        action = menu.addAction("InlineComponent（フェライト等）を追加・編集...")
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is action:
            cable_type = self._text(row, 5)
            label = f"No.{no_item.text()} {cable_type}".strip()
            dialog = InlineComponentDialog(self._handle.connection, cable_id, label, self)
            dialog.exec()


def _parse_float(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
