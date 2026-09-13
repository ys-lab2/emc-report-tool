from __future__ import annotations

from PySide6.QtWidgets import QLabel, QScrollArea, QTextEdit, QVBoxLayout, QWidget

from repositories import medical_repository
from services.project_service import ProjectHandle

LARGE_HEIGHT = 180


class MedicalPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._criteria = None
        self._loading = False

        self.basic_safety_edit = QTextEdit()
        self.basic_performance_edit = QTextEdit()
        self.immunity_performance_edit = QTextEdit()

        for edit in (self.basic_safety_edit, self.basic_performance_edit, self.immunity_performance_edit):
            edit.setMinimumHeight(LARGE_HEIGHT)

        self.basic_safety_edit.setPlaceholderText("1行につき1項目で判定基準を記入してください。")
        self.basic_performance_edit.setPlaceholderText("1行につき1項目で判定基準を記入してください。")
        self.immunity_performance_edit.setPlaceholderText("イミュニティ試験時の性能基準を自由に記入してください。")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.addWidget(QLabel("B.1 基礎安全　判定基準"))
        form_layout.addWidget(self.basic_safety_edit)
        form_layout.addWidget(QLabel("B.2 基本性能　判定基準"))
        form_layout.addWidget(self.basic_performance_edit)
        form_layout.addWidget(QLabel("B.3 イミュニティ試験時の性能基準"))
        form_layout.addWidget(self.immunity_performance_edit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        self.basic_safety_edit.textChanged.connect(self._save)
        self.basic_performance_edit.textChanged.connect(self._save)
        self.immunity_performance_edit.textChanged.connect(self._save)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        conn = self._handle.connection
        self._criteria = medical_repository.get_or_create(conn, self._handle.project.project_id)

        safety_items = medical_repository.list_items(conn, self._criteria.medical_criteria_id, "basic_safety")
        performance_items = medical_repository.list_items(conn, self._criteria.medical_criteria_id, "basic_performance")

        self.basic_safety_edit.setPlainText("\n".join(i.content for i in safety_items))
        self.basic_performance_edit.setPlainText("\n".join(i.content for i in performance_items))
        self.immunity_performance_edit.setPlainText(self._criteria.immunity_performance_text)
        self._loading = False

    def _save(self) -> None:
        if self._handle is None or self._loading or self._criteria is None:
            return
        conn = self._handle.connection

        safety_lines = [line for line in self.basic_safety_edit.toPlainText().split("\n") if line.strip()]
        performance_lines = [line for line in self.basic_performance_edit.toPlainText().split("\n") if line.strip()]
        medical_repository.replace_items(conn, self._criteria.medical_criteria_id, "basic_safety", safety_lines)
        medical_repository.replace_items(conn, self._criteria.medical_criteria_id, "basic_performance", performance_lines)

        self._criteria.immunity_performance_text = self.immunity_performance_edit.toPlainText()
        medical_repository.update(conn, self._criteria)
