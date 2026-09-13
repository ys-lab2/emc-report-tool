from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.taiwan import InternalComponent
from repositories import taiwan_repository
from services.project_service import ProjectHandle

LARGE_HEIGHT = 160
COMPONENT_COLUMNS = ["装置名", "数量(Max)", "モデル名", "製造者"]
COMPONENT_ID_ROLE = 1001


class TaiwanPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._applicant = None
        self._loading = False

        self.company_en_edit = QLineEdit()
        self.address_en_edit = QLineEdit()
        self.company_zh_edit = QLineEdit()
        self.address_zh_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMinimumHeight(100)

        applicant_form = QFormLayout()
        applicant_form.addRow("会社名（英語）", self.company_en_edit)
        applicant_form.addRow("住所（英語）", self.address_en_edit)
        applicant_form.addRow("会社名（繁体字）", self.company_zh_edit)
        applicant_form.addRow("住所（繁体字）", self.address_zh_edit)
        applicant_form.addRow("備考", self.notes_edit)

        self.component_table = QTableWidget(0, len(COMPONENT_COLUMNS))
        self.component_table.setHorizontalHeaderLabels(COMPONENT_COLUMNS)
        self.component_table.horizontalHeader().setStretchLastSection(True)
        self.component_table.itemChanged.connect(self._on_component_item_changed)

        add_component_button = QPushButton("+ 内部構成品を追加")
        delete_component_button = QPushButton("削除")
        add_component_button.clicked.connect(self._add_component)
        delete_component_button.clicked.connect(self._delete_selected_component)

        component_toolbar = QHBoxLayout()
        component_toolbar.addWidget(add_component_button)
        component_toolbar.addWidget(delete_component_button)
        component_toolbar.addStretch(1)

        self.eut_status_edit = QTextEdit()
        self.eut_status_edit.setMinimumHeight(LARGE_HEIGHT)
        self.eut_status_edit.setPlaceholderText(
            "試験配置後、電源投入時からのEUT動作を詳細な文章または箇条書きで自由に記入してください。"
        )

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.addWidget(QLabel("C.1 申請者情報（※台湾輸入代理店）"))
        form_layout.addLayout(applicant_form)
        form_layout.addWidget(QLabel("C.2 EUTの内部構成品リスト"))
        form_layout.addLayout(component_toolbar)
        form_layout.addWidget(self.component_table)
        form_layout.addWidget(QLabel("C.3 試験時のEUTの動作状態"))
        form_layout.addWidget(self.eut_status_edit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        for edit in (self.company_en_edit, self.address_en_edit, self.company_zh_edit, self.address_zh_edit):
            edit.editingFinished.connect(self._save_applicant)
        self.notes_edit.textChanged.connect(self._save_applicant)
        self.eut_status_edit.textChanged.connect(self._save_applicant)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        conn = self._handle.connection
        applicant = taiwan_repository.get_or_create(conn, self._handle.project.project_id)
        self._applicant = applicant

        self.company_en_edit.setText(applicant.company_name_en)
        self.address_en_edit.setText(applicant.address_en)
        self.company_zh_edit.setText(applicant.company_name_zh)
        self.address_zh_edit.setText(applicant.address_zh)
        self.notes_edit.setPlainText(applicant.notes)
        self.eut_status_edit.setPlainText(applicant.eut_operation_status_text)

        self.component_table.setRowCount(0)
        for component in taiwan_repository.list_internal_components(conn, applicant.taiwan_applicant_id):
            self._append_component_row(component)

        self._loading = False

    def _save_applicant(self) -> None:
        if self._handle is None or self._loading or self._applicant is None:
            return
        self._applicant.company_name_en = self.company_en_edit.text()
        self._applicant.address_en = self.address_en_edit.text()
        self._applicant.company_name_zh = self.company_zh_edit.text()
        self._applicant.address_zh = self.address_zh_edit.text()
        self._applicant.notes = self.notes_edit.toPlainText()
        self._applicant.eut_operation_status_text = self.eut_status_edit.toPlainText()
        taiwan_repository.update(self._handle.connection, self._applicant)

    # --- 内部構成品リスト ---

    def _append_component_row(self, component: InternalComponent) -> None:
        row = self.component_table.rowCount()
        self.component_table.insertRow(row)

        name_item = QTableWidgetItem(component.device_name)
        name_item.setData(COMPONENT_ID_ROLE, component.internal_component_id)
        self.component_table.setItem(row, 0, name_item)
        self.component_table.setItem(row, 1, QTableWidgetItem(component.quantity_max))
        self.component_table.setItem(row, 2, QTableWidgetItem(component.model_name))
        self.component_table.setItem(row, 3, QTableWidgetItem(component.manufacturer))

    def _on_component_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        self._save_component_row(item.row())

    def _save_component_row(self, row: int) -> None:
        if self._handle is None or self._loading or self._applicant is None:
            return
        name_item = self.component_table.item(row, 0)
        if name_item is None:
            return
        component_id = name_item.data(COMPONENT_ID_ROLE)

        component = InternalComponent(
            internal_component_id=component_id,
            taiwan_applicant_id=self._applicant.taiwan_applicant_id,
            device_name=self._component_text(row, 0),
            quantity_max=self._component_text(row, 1),
            model_name=self._component_text(row, 2),
            manufacturer=self._component_text(row, 3),
            sort_order=row,
        )
        taiwan_repository.update_internal_component(self._handle.connection, component)

    def _component_text(self, row: int, column: int) -> str:
        item = self.component_table.item(row, column)
        return item.text() if item else ""

    def _add_component(self) -> None:
        if self._handle is None or self._applicant is None:
            return
        component = taiwan_repository.add_internal_component(
            self._handle.connection,
            InternalComponent(
                internal_component_id="",
                taiwan_applicant_id=self._applicant.taiwan_applicant_id,
                sort_order=self.component_table.rowCount(),
            ),
        )
        self._append_component_row(component)

    def _delete_selected_component(self) -> None:
        if self._handle is None:
            return
        row = self.component_table.currentRow()
        if row < 0:
            return
        name_item = self.component_table.item(row, 0)
        if name_item is None:
            return
        component_id = name_item.data(COMPONENT_ID_ROLE)
        taiwan_repository.delete_internal_component(self._handle.connection, component_id)
        self.component_table.removeRow(row)
