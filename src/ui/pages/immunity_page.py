from __future__ import annotations

from PySide6.QtWidgets import QLabel, QScrollArea, QTextEdit, QVBoxLayout, QWidget

from repositories import immunity_repository
from services.project_service import ProjectHandle

LARGE_HEIGHT = 180


class ImmunityPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._criteria = None
        self._loading = False

        self.criterion_a_edit = QTextEdit()
        self.criterion_b_edit = QTextEdit()
        self.criterion_c_edit = QTextEdit()
        self.verification_points_edit = QTextEdit()

        for edit in (self.criterion_a_edit, self.criterion_b_edit, self.criterion_c_edit, self.verification_points_edit):
            edit.setMinimumHeight(LARGE_HEIGHT)

        self.verification_points_edit.setPlaceholderText("1行につき1項目で自由に記入してください（例：表示確認、音声確認、通信確認）。")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.addWidget(QLabel("A.1 イミュニティー試験時の性能基準　※医療機器は「医療規格」ページに記載"))
        form_layout.addWidget(QLabel("Performance criterion A"))
        form_layout.addWidget(self.criterion_a_edit)
        form_layout.addWidget(QLabel("Performance criterion B"))
        form_layout.addWidget(self.criterion_b_edit)
        form_layout.addWidget(QLabel("Performance criterion C"))
        form_layout.addWidget(self.criterion_c_edit)
        form_layout.addWidget(QLabel("動作確認箇所"))
        form_layout.addWidget(self.verification_points_edit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        self.criterion_a_edit.textChanged.connect(self._save)
        self.criterion_b_edit.textChanged.connect(self._save)
        self.criterion_c_edit.textChanged.connect(self._save)
        self.verification_points_edit.textChanged.connect(self._save)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        conn = self._handle.connection
        self._criteria = immunity_repository.get_or_create(conn, self._handle.project.project_id)

        self.criterion_a_edit.setPlainText(self._criteria.criterion_a)
        self.criterion_b_edit.setPlainText(self._criteria.criterion_b)
        self.criterion_c_edit.setPlainText(self._criteria.criterion_c)

        points = immunity_repository.list_verification_points(conn, self._criteria.immunity_criteria_id)
        self.verification_points_edit.setPlainText("\n".join(p.content for p in points))
        self._loading = False

    def _save(self) -> None:
        if self._handle is None or self._loading or self._criteria is None:
            return
        conn = self._handle.connection
        self._criteria.criterion_a = self.criterion_a_edit.toPlainText()
        self._criteria.criterion_b = self.criterion_b_edit.toPlainText()
        self._criteria.criterion_c = self.criterion_c_edit.toPlainText()
        immunity_repository.update(conn, self._criteria)

        lines = [line for line in self.verification_points_edit.toPlainText().split("\n") if line.strip()]
        immunity_repository.replace_verification_points(conn, self._criteria.immunity_criteria_id, lines)
