from __future__ import annotations

from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from diagram.layout import auto_layout
from diagram.scene import DiagramScene
from diagram.view import DiagramView
from models.ground_connection import GROUND_KINDS, GroundConnection
from models.power_source import POWER_SOURCE_KINDS, PowerSource
from services import ground_connection_service, power_source_service
from services.project_service import ProjectHandle


class DiagramPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._handle: ProjectHandle | None = None

        self.undo_stack = QUndoStack(self)
        self.scene = DiagramScene(self.undo_stack)
        self.view = DiagramView()
        self.view.setScene(self.scene)

        undo_button = QPushButton("Undo")
        redo_button = QPushButton("Redo")
        zoom_in_button = QPushButton("ズーム+")
        zoom_out_button = QPushButton("ズーム-")
        fit_button = QPushButton("Fit to View")
        auto_layout_button = QPushButton("自動配置")
        add_power_button = QPushButton("+ 電源")
        add_ground_button = QPushButton("+ GND")

        undo_button.clicked.connect(self.undo_stack.undo)
        redo_button.clicked.connect(self.undo_stack.redo)
        zoom_in_button.clicked.connect(self.view.zoom_in)
        zoom_out_button.clicked.connect(self.view.zoom_out)
        fit_button.clicked.connect(self.view.fit_to_view)
        auto_layout_button.clicked.connect(self._on_auto_layout)
        add_power_button.clicked.connect(self._on_add_power_source)
        add_ground_button.clicked.connect(self._on_add_ground_connection)

        undo_button.setShortcut("Ctrl+Z")
        redo_button.setShortcut("Ctrl+Y")
        fit_button.setShortcut("F")

        toolbar = QHBoxLayout()
        for button in (
            undo_button,
            redo_button,
            zoom_in_button,
            zoom_out_button,
            fit_button,
            auto_layout_button,
            add_power_button,
            add_ground_button,
        ):
            toolbar.addWidget(button)
        toolbar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.view)

    def set_project(self, handle: ProjectHandle) -> None:
        self._handle = handle
        self.scene.set_project(handle.connection, handle.project.project_id)
        self.undo_stack.clear()

    def refresh(self) -> None:
        if self._handle is None:
            return
        self.scene.reload()

    def _on_auto_layout(self) -> None:
        if self._handle is None:
            return
        reply = QMessageBox.question(
            self,
            "自動配置",
            "現在の手動調整はすべて上書きされます。自動配置を実行しますか？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        auto_layout.layout_all(self._handle.connection, self._handle.project.project_id)
        self.refresh()

    def _on_add_power_source(self) -> None:
        if self._handle is None:
            return
        kind, ok = QInputDialog.getItem(self, "電源を追加", "種類", list(POWER_SOURCE_KINDS), editable=False)
        if not ok:
            return
        power_source_service.create_power_source(
            self._handle.connection,
            PowerSource(power_source_id="", project_id=self._handle.project.project_id, kind=kind),
        )
        self.refresh()

    def _on_add_ground_connection(self) -> None:
        if self._handle is None:
            return
        kind, ok = QInputDialog.getItem(self, "GNDを追加", "種類", list(GROUND_KINDS), editable=False)
        if not ok:
            return
        ground_connection_service.create_ground_connection(
            self._handle.connection,
            GroundConnection(ground_connection_id="", project_id=self._handle.project.project_id, kind=kind),
        )
        self.refresh()
