from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QVBoxLayout, QWidget

from models.applicant import Applicant
from repositories import applicant_repository
from services.project_service import ProjectHandle


class ApplicantPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None
        self._applicant: Applicant | None = None
        self._loading = False

        self.company_jp_edit = QLineEdit()
        self.company_en_edit = QLineEdit()
        self.address_jp_edit = QLineEdit()
        self.address_en_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("会社名（和文）", self.company_jp_edit)
        form.addRow("会社名（英文）", self.company_en_edit)
        form.addRow("住所（和文）", self.address_jp_edit)
        form.addRow("住所（英文）", self.address_en_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch(1)

        for edit in (self.company_jp_edit, self.company_en_edit, self.address_jp_edit, self.address_en_edit):
            edit.editingFinished.connect(self._save)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self._loading = True
        conn = self._handle.connection
        applicant = applicant_repository.get_by_project(conn, self._handle.project.project_id)
        if applicant is None:
            applicant = Applicant(applicant_id="", project_id=self._handle.project.project_id)
        self._applicant = applicant

        self.company_jp_edit.setText(applicant.company_name_jp)
        self.company_en_edit.setText(applicant.company_name_en)
        self.address_jp_edit.setText(applicant.address_jp)
        self.address_en_edit.setText(applicant.address_en)
        self._loading = False

    def _save(self) -> None:
        if self._handle is None or self._loading or self._applicant is None:
            return
        self._applicant.company_name_jp = self.company_jp_edit.text()
        self._applicant.company_name_en = self.company_en_edit.text()
        self._applicant.address_jp = self.address_jp_edit.text()
        self._applicant.address_en = self.address_en_edit.text()
        self._applicant = applicant_repository.upsert(self._handle.connection, self._applicant)
