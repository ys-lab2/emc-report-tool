from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFontDialog,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
)

import config as config_module
from services import backup_service, project_service
from services.project_service import ProjectHandle
from ui.pages.applicant_page import ApplicantPage
from ui.pages.cable_list_page import CableListPage
from ui.pages.countermeasure_page import CountermeasurePage
from ui.pages.diagram_page import DiagramPage
from ui.pages.equipment_list_page import EquipmentListPage
from ui.pages.eut_overview_page import EutOverviewPage
from ui.pages.export_page import ExportPage
from ui.pages.immunity_page import ImmunityPage
from ui.pages.medical_page import MedicalPage
from ui.pages.operation_mode_page import OperationModePage
from ui.pages.placeholder_page import PlaceholderPage
from ui.pages.project_page import ProjectPage
from ui.pages.taiwan_page import TaiwanPage

logger = logging.getLogger(__name__)

# 「接続情報」は独立画面を設けない。ケーブルリストのFrom/Toが接続情報そのものであり、
# 構成図が接続情報のグラフィカル表示を兼ねるため（ui-design.md 6.節）。
NAV_ITEMS = [
    ("プロジェクト", "project"),
    ("申請者", "applicant"),
    ("装置概要", "eut_overview"),
    ("動作モード", "operation_mode"),
    ("機器リスト", "equipment"),
    ("ケーブルリスト", "cable"),
    ("構成図", "diagram"),
    ("EMC対策", "countermeasure"),
    ("イミュニティ", "immunity"),
    ("医療規格", "medical"),
    ("台湾資料", "taiwan"),
    ("顧客資料インポート", "import"),
    ("出力", "export"),
]

PHASE_NOT_READY_MESSAGE = "この画面は今後のPhaseで実装予定です。"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EMCテストレポート作成資料アプリ")
        self.resize(1280, 800)

        self._config = config_module.load_config()
        self._handle: ProjectHandle | None = None

        self.nav_list = QListWidget()
        for label, _key in NAV_ITEMS:
            self.nav_list.addItem(label)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        self.pages: dict[str, object] = {
            "project": ProjectPage(),
            "applicant": ApplicantPage(),
            "eut_overview": EutOverviewPage(),
            "operation_mode": OperationModePage(),
            "equipment": EquipmentListPage(),
            "cable": CableListPage(),
            "diagram": DiagramPage(),
            "countermeasure": CountermeasurePage(),
            "immunity": ImmunityPage(),
            "medical": MedicalPage(),
            "taiwan": TaiwanPage(),
            "import": PlaceholderPage(PHASE_NOT_READY_MESSAGE),
            "export": ExportPage(),
        }

        self.stack = QStackedWidget()
        for _label, key in NAV_ITEMS:
            self.stack.addWidget(self.pages[key])

        splitter = QSplitter()
        splitter.addWidget(self.nav_list)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 1080])
        self.setCentralWidget(splitter)

        self.nav_list.setCurrentRow(0)

        self.setStatusBar(QStatusBar())
        self._update_status_bar("プロジェクトが開かれていません。")

        self._build_menu()
        self._set_project_pages_enabled(False)

        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._on_autosave_tick)
        self._restart_autosave_timer()

    # --- ナビゲーション ---
    def _on_nav_changed(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        _label, key = NAV_ITEMS[row]
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

    def _set_project_pages_enabled(self, enabled: bool) -> None:
        self.stack.setEnabled(enabled)

    # --- メニュー ---
    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル(&F)")

        new_action = file_menu.addAction("新規作成(&N)")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_project)

        open_action = file_menu.addAction("開く(&O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_project)

        self.recent_menu = file_menu.addMenu("最近使用したプロジェクト")
        self.recent_menu.aboutToShow.connect(self._rebuild_recent_menu)

        file_menu.addSeparator()

        save_action = file_menu.addAction("保存(&S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_project)

        save_as_action = file_menu.addAction("名前を付けて保存(&A)")
        save_as_action.triggered.connect(self._on_save_as_project)

        file_menu.addSeparator()
        exit_action = file_menu.addAction("終了")
        exit_action.triggered.connect(self.close)

        view_menu = menu_bar.addMenu("表示(&V)")
        font_action = view_menu.addAction("フォントを変更...")
        font_action.triggered.connect(self._on_change_font)

    def _on_change_font(self) -> None:
        current_font = QFont(self._config.font_family, self._config.font_size)
        font, ok = QFontDialog.getFont(current_font, self, "フォントを選択")
        if not ok:
            return

        self._config.font_family = font.family()
        self._config.font_size = font.pointSize() if font.pointSize() > 0 else self._config.font_size
        config_module.save_config(self._config)

        QApplication.instance().setFont(QFont(self._config.font_family, self._config.font_size))

        for page in self.pages.values():
            if hasattr(page, "refresh"):
                page.refresh()

    def _rebuild_recent_menu(self) -> None:
        self.recent_menu.clear()
        if not self._config.recent_projects:
            action = self.recent_menu.addAction("（履歴がありません）")
            action.setEnabled(False)
            return
        for path_str in self._config.recent_projects:
            action = self.recent_menu.addAction(path_str)
            action.triggered.connect(lambda checked=False, p=path_str: self._open_project_path(p))

    # --- プロジェクト操作 ---
    def _on_new_project(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "新規プロジェクト作成", "", "EMCプロジェクト (*.emcproj)"
        )
        if not file_path:
            return
        if not file_path.endswith(".emcproj"):
            file_path += ".emcproj"

        try:
            handle = project_service.create_new(file_path)
        except FileExistsError as exc:
            QMessageBox.warning(self, "作成できません", str(exc))
            return

        self._set_handle(handle)

    def _on_open_project(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "プロジェクトを開く", "", "EMCプロジェクト (*.emcproj)"
        )
        if not file_path:
            return
        self._open_project_path(file_path)

    def _open_project_path(self, file_path: str) -> None:
        try:
            handle = project_service.open_project(file_path)
        except (FileNotFoundError, ValueError) as exc:
            QMessageBox.warning(self, "開けません", str(exc))
            return
        self._set_handle(handle)

    def _on_save_project(self) -> None:
        if self._handle is None:
            return
        project_service.save(self._handle)
        self._update_status_bar(f"保存しました: {self._handle.file_path.name}")

    def _on_save_as_project(self) -> None:
        if self._handle is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "", "EMCプロジェクト (*.emcproj)"
        )
        if not file_path:
            return
        if not file_path.endswith(".emcproj"):
            file_path += ".emcproj"

        try:
            new_handle = project_service.save_as(self._handle, file_path)
        except FileExistsError as exc:
            QMessageBox.warning(self, "保存できません", str(exc))
            return

        self._set_handle(new_handle)

    def _set_handle(self, handle: ProjectHandle) -> None:
        if self._handle is not None:
            self._handle.close()
        self._handle = handle

        self._config.add_recent_project(str(handle.file_path))
        config_module.save_config(self._config)

        for page in self.pages.values():
            if hasattr(page, "set_project"):
                page.set_project(handle)

        self._set_project_pages_enabled(True)
        self.setWindowTitle(f"EMCテストレポート作成資料アプリ - {handle.file_path.name}")
        self._update_status_bar(f"開いています: {handle.file_path}")
        self._restart_autosave_timer()

    # --- 自動保存・バックアップ ---
    def _restart_autosave_timer(self) -> None:
        interval_ms = self._config.autosave_interval_seconds * 1000
        self._autosave_timer.start(interval_ms)

    def _on_autosave_tick(self) -> None:
        if self._handle is None:
            return
        try:
            project_service.save(self._handle)
            backup_path = backup_service.create_backup(self._handle, self._config.backup_generations)
            logger.info("Autosave backup created: %s", backup_path)
            self._update_status_bar(f"自動保存しました（{backup_path.name}）")
        except OSError:
            logger.exception("Autosave failed")

    def _update_status_bar(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qtのオーバーライド規約
        if self._handle is not None:
            try:
                project_service.save(self._handle)
            except OSError:
                logger.exception("Failed to save on close")
            self._handle.close()
        super().closeEvent(event)
