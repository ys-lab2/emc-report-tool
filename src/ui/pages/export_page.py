from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from exporters.word import fm05_v36
from services import export_service
from services.project_service import ProjectHandle

logger = logging.getLogger(__name__)


class ExportPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None

        self.template_label = QLabel()
        self.status_label = QLabel("")

        export_word_button = QPushButton("Word出力...")
        export_word_button.clicked.connect(self._on_export_word)

        export_pdf_button = QPushButton("Word→PDF出力...")
        export_pdf_button.clicked.connect(self._on_export_pdf)

        layout = QVBoxLayout(self)
        layout.addWidget(self.template_label)
        layout.addWidget(export_word_button)
        layout.addWidget(export_pdf_button)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.refresh()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self.template_label.setText(
            f"テンプレート: {fm05_v36.TEMPLATE_ID} Ver.{fm05_v36.TEMPLATE_VERSION}\n"
            f"(テンプレートファイル: {export_service.DEFAULT_TEMPLATE_FILENAME})"
        )
        self.status_label.setText("")

    def _on_export_word(self) -> None:
        self._run_export(
            dialog_title="Word出力先を選択",
            file_filter="Wordファイル (*.docx)",
            default_suffix=".docx",
            export_func=export_service.export_to_word,
            success_message="Wordファイルを出力しました。",
        )

    def _on_export_pdf(self) -> None:
        self._run_export(
            dialog_title="PDF出力先を選択",
            file_filter="PDFファイル (*.pdf)",
            default_suffix=".pdf",
            export_func=export_service.export_to_pdf,
            success_message="PDFファイルを出力しました。",
        )

    def _run_export(
        self,
        dialog_title: str,
        file_filter: str,
        default_suffix: str,
        export_func: Callable[[ProjectHandle, Path], Path],
        success_message: str,
    ) -> None:
        if self._handle is None:
            return

        default_name = self._handle.file_path.stem + default_suffix
        output_path_str, _ = QFileDialog.getSaveFileName(self, dialog_title, default_name, file_filter)
        if not output_path_str:
            return
        output_path = Path(output_path_str)
        if not output_path.suffix:
            output_path = output_path.with_suffix(default_suffix)

        self.status_label.setText("出力中です。しばらくお待ちください...")
        self.setEnabled(False)
        try:
            export_func(self._handle, output_path)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "出力できません", str(exc))
            self.status_label.setText("")
            return
        except Exception:
            logger.exception("Export failed")
            QMessageBox.critical(
                self, "エラー", "処理中にエラーが発生しました。詳細はログを確認してください。"
            )
            self.status_label.setText("")
            return
        finally:
            self.setEnabled(True)

        self.status_label.setText(f"出力しました: {output_path}")
        QMessageBox.information(self, "完了", f"{success_message}\n{output_path}")
