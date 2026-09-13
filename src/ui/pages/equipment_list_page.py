from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.equipment import Equipment
from repositories import equipment_repository
from services import equipment_service
from services.project_service import ProjectHandle
from ui.dialogs.equipment_edit_dialog import EquipmentEditDialog

PLACEMENT_LABELS = {
    "standalone": "独立",
    "embedded": "内蔵",
    "inserted": "内蔵",
    "attached": "外付け",
}

EQUIPMENT_ID_ROLE = Qt.UserRole


class EquipmentListPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["ID", "機器名", "モデル名", "シリアル", "配置"])
        self.tree.itemDoubleClicked.connect(lambda *_: self._edit_selected())

        add_button = QPushButton("+ 新規機器")
        edit_button = QPushButton("編集")
        delete_button = QPushButton("削除")
        add_button.clicked.connect(self._add_equipment)
        edit_button.clicked.connect(self._edit_selected)
        delete_button.clicked.connect(self._delete_selected)

        toolbar = QHBoxLayout()
        toolbar.addWidget(add_button)
        toolbar.addWidget(edit_button)
        toolbar.addWidget(delete_button)
        toolbar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.tree)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        if self._handle is None:
            return

        equipments = equipment_repository.list_by_project(
            self._handle.connection, self._handle.project.project_id
        )
        by_parent: dict[str | None, list[Equipment]] = {}
        for eq in equipments:
            by_parent.setdefault(eq.parent_equipment_id, []).append(eq)

        def build(parent_item: QTreeWidget | QTreeWidgetItem, parent_id: str | None) -> None:
            for eq in by_parent.get(parent_id, []):
                item = QTreeWidgetItem(
                    [
                        eq.display_id,
                        eq.description,
                        eq.model_name,
                        eq.serial,
                        PLACEMENT_LABELS.get(eq.placement_type, eq.placement_type),
                    ]
                )
                item.setData(0, EQUIPMENT_ID_ROLE, eq.equipment_id)
                parent_item.addChild(item) if isinstance(parent_item, QTreeWidgetItem) else self.tree.addTopLevelItem(item)
                build(item, eq.equipment_id)

        build(self.tree, None)
        self.tree.expandAll()
        for i in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(i)

    def _selected_equipment_id(self) -> str | None:
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, EQUIPMENT_ID_ROLE)

    def _add_equipment(self) -> None:
        if self._handle is None:
            return
        dialog = EquipmentEditDialog(self._handle.connection, self._handle.project.project_id, None, self)
        if dialog.exec():
            self.refresh()

    def _edit_selected(self) -> None:
        if self._handle is None:
            return
        equipment_id = self._selected_equipment_id()
        if equipment_id is None:
            return
        equipment = equipment_repository.get(self._handle.connection, equipment_id)
        if equipment is None:
            return
        dialog = EquipmentEditDialog(self._handle.connection, self._handle.project.project_id, equipment, self)
        if dialog.exec():
            self.refresh()

    def _delete_selected(self) -> None:
        if self._handle is None:
            return
        equipment_id = self._selected_equipment_id()
        if equipment_id is None:
            return

        conn = self._handle.connection
        impact = equipment_service.get_deletion_impact(conn, equipment_id)
        cascade_children = False

        if impact.direct_children:
            box = QMessageBox(self)
            box.setWindowTitle("内包されている機器があります")
            box.setText(
                f"この機器には内包されている機器が{len(impact.direct_children)}件あります。\n"
                "子機器も削除しますか？"
            )
            delete_children_button = box.addButton("子機器も削除する", QMessageBox.DestructiveRole)
            independent_button = box.addButton("子機器を独立機器に変更する", QMessageBox.ActionRole)
            box.addButton("キャンセル", QMessageBox.RejectRole)
            box.exec()

            clicked = box.clickedButton()
            if clicked is delete_children_button:
                cascade_children = True
            elif clicked is independent_button:
                cascade_children = False
            else:
                return
        elif impact.referencing_cable_count > 0:
            reply = QMessageBox.question(
                self,
                "確認",
                f"この機器には{impact.referencing_cable_count}本のケーブルが接続されています。\n"
                "機器を削除すると関連する接続情報も削除されます。\n続行しますか？",
            )
            if reply != QMessageBox.Yes:
                return

        equipment_service.delete_equipment(conn, equipment_id, cascade_children=cascade_children)
        self.refresh()
