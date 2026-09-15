import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from models.cable import Cable
from models.equipment import Equipment
from services import cable_service, equipment_service, project_service
from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_opens_project_and_navigates(qapp, tmp_path, monkeypatch):
    import config as config_module

    monkeypatch.setattr(config_module, "config_file_path", lambda: tmp_path / "config.json")

    window = MainWindow()

    project_path = tmp_path / "PJ_SMOKE.emcproj"
    handle = project_service.create_new(project_path)
    window._set_handle(handle)

    conn = handle.connection
    project_id = handle.project.project_id

    equipment_a = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT")
    )
    equipment_b = equipment_service.create_equipment(
        conn,
        Equipment(
            equipment_id="",
            project_id=project_id,
            display_id="B",
            category="EUT",
            placement_type="embedded",
            parent_equipment_id=equipment_a.equipment_id,
        ),
    )
    cable_service.create_cable(
        conn,
        Cable(
            cable_id="",
            project_id=project_id,
            from_ref_id=equipment_a.equipment_id,
            to_ref_id=equipment_b.equipment_id,
            cable_type="USB",
        ),
    )

    for row in range(window.nav_list.count()):
        window.nav_list.setCurrentRow(row)

    equipment_page = window.pages["equipment"]
    equipment_page.refresh()
    assert equipment_page.tree.topLevelItemCount() == 1
    assert equipment_page.tree.topLevelItem(0).childCount() == 1

    cable_page = window.pages["cable"]
    cable_page.refresh()
    assert cable_page.table.rowCount() == 1

    window._handle.close()


def test_project_page_edits_persist(qapp, tmp_path, monkeypatch):
    import config as config_module

    monkeypatch.setattr(config_module, "config_file_path", lambda: tmp_path / "config2.json")

    window = MainWindow()
    project_path = tmp_path / "PJ_SMOKE2.emcproj"
    handle = project_service.create_new(project_path)
    window._set_handle(handle)

    project_page = window.pages["project"]
    project_page.project_no_edit.setText("PJ260099")
    project_page._save()

    reloaded = project_service.open_project(project_path)
    assert reloaded.project.project_no == "PJ260099"
    reloaded.close()

    window._handle.close()
