from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.report_standard import ReportStandard
from repositories import report_standard_repository
from services import project_service
from services.project_service import ProjectHandle

STANDARD_COLUMNS = ["規格名", "和文/英文", "希望納期", "提出媒体"]
LANGUAGE_OPTIONS = [("jp", "和文"), ("en", "英文")]
STANDARD_ID_ROLE = 1001


class ProjectPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._loading = False

        self.project_no_edit = QLineEdit()
        self.test_plan_no_edit = QLineEdit()
        self.measurement_period_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(100)

        form = QFormLayout()
        form.addRow("プロジェクト番号", self.project_no_edit)
        form.addRow("テストプラン番号", self.test_plan_no_edit)
        form.addRow("測定期間", self.measurement_period_edit)
        form.addRow("備考", self.notes_edit)

        self.standards_table = QTableWidget(0, len(STANDARD_COLUMNS))
        self.standards_table.setHorizontalHeaderLabels(STANDARD_COLUMNS)
        self.standards_table.horizontalHeader().setStretchLastSection(True)
        self.standards_table.itemChanged.connect(self._on_standard_item_changed)

        add_standard_button = QPushButton("+ 規格を追加")
        delete_standard_button = QPushButton("削除")
        add_standard_button.clicked.connect(self._add_standard)
        delete_standard_button.clicked.connect(self._delete_selected_standard)

        standard_toolbar = QHBoxLayout()
        standard_toolbar.addWidget(add_standard_button)
        standard_toolbar.addWidget(delete_standard_button)
        standard_toolbar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("レポート作成規格（最大8件、Word帳票の表に対応）"))
        layout.addLayout(standard_toolbar)
        layout.addWidget(self.standards_table)

        self.project_no_edit.editingFinished.connect(self._save)
        self.test_plan_no_edit.editingFinished.connect(self._save)
        self.measurement_period_edit.editingFinished.connect(self._save)
        self.notes_edit.textChanged.connect(self._save)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        project = self._handle.project
        self.project_no_edit.setText(project.project_no)
        self.test_plan_no_edit.setText(project.test_plan_no)
        self.measurement_period_edit.setText(project.measurement_period)
        self.notes_edit.setPlainText(project.notes)

        self.standards_table.setRowCount(0)
        for standard in report_standard_repository.list_by_project(
            self._handle.connection, project.project_id
        ):
            self._append_standard_row(standard)

        self._loading = False

    def _save(self) -> None:
        if self._handle is None or self._loading:
            return
        project = self._handle.project
        project.project_no = self.project_no_edit.text()
        project.test_plan_no = self.test_plan_no_edit.text()
        project.measurement_period = self.measurement_period_edit.text()
        project.notes = self.notes_edit.toPlainText()
        project_service.save(self._handle)

    # --- レポート作成規格 ---

    def _append_standard_row(self, standard: ReportStandard) -> None:
        row = self.standards_table.rowCount()
        self.standards_table.insertRow(row)

        name_item = QTableWidgetItem(standard.standard_name)
        name_item.setData(STANDARD_ID_ROLE, standard.report_standard_id)
        self.standards_table.setItem(row, 0, name_item)

        language_combo = QComboBox()
        for code, label in LANGUAGE_OPTIONS:
            language_combo.addItem(label, code)
        index = language_combo.findData(standard.language)
        if index >= 0:
            language_combo.setCurrentIndex(index)
        language_combo.currentIndexChanged.connect(lambda _=None, r=row: self._save_standard_row(r))
        self.standards_table.setCellWidget(row, 1, language_combo)

        self.standards_table.setItem(row, 2, QTableWidgetItem(standard.desired_due_date))
        self.standards_table.setItem(row, 3, QTableWidgetItem(standard.submission_media))

    def _on_standard_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        self._save_standard_row(item.row())

    def _save_standard_row(self, row: int) -> None:
        if self._handle is None or self._loading:
            return
        name_item = self.standards_table.item(row, 0)
        if name_item is None:
            return
        standard_id = name_item.data(STANDARD_ID_ROLE)
        language_combo: QComboBox = self.standards_table.cellWidget(row, 1)

        standard = ReportStandard(
            report_standard_id=standard_id,
            project_id=self._handle.project.project_id,
            standard_name=self._standard_text(row, 0),
            language=language_combo.currentData(),
            desired_due_date=self._standard_text(row, 2),
            submission_media=self._standard_text(row, 3),
            sort_order=row,
        )
        report_standard_repository.update(self._handle.connection, standard)

    def _standard_text(self, row: int, column: int) -> str:
        item = self.standards_table.item(row, column)
        return item.text() if item else ""

    def _add_standard(self) -> None:
        if self._handle is None:
            return
        if self.standards_table.rowCount() >= 8:
            return
        standard = report_standard_repository.add(
            self._handle.connection,
            ReportStandard(
                report_standard_id="",
                project_id=self._handle.project.project_id,
                submission_media="PDF",
                sort_order=self.standards_table.rowCount(),
            ),
        )
        self._append_standard_row(standard)

    def _delete_selected_standard(self) -> None:
        if self._handle is None:
            return
        row = self.standards_table.currentRow()
        if row < 0:
            return
        name_item = self.standards_table.item(row, 0)
        if name_item is None:
            return
        standard_id = name_item.data(STANDARD_ID_ROLE)
        report_standard_repository.delete(self._handle.connection, standard_id)
        self.standards_table.removeRow(row)
