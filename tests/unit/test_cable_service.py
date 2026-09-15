import pytest

from models.cable import Cable
from models.equipment import Equipment
from services import cable_service, equipment_service
from services.cable_service import InvalidEquipmentReferenceError


def make_equipment(project_id, display_id):
    return Equipment(equipment_id="", project_id=project_id, display_id=display_id, category="EUT")


def test_create_cable_auto_numbers(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))

    c1 = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )
    c2 = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )

    assert c1.cable_no == 1
    assert c2.cable_no == 2


def test_create_cable_rejects_missing_equipment(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))

    with pytest.raises(InvalidEquipmentReferenceError):
        cable_service.create_cable(
            conn,
            Cable(
                cable_id="",
                project_id=project.project_id,
                from_ref_id=a.equipment_id,
                to_ref_id="does-not-exist",
            ),
        )


def test_multiple_cables_between_same_pair_allowed(conn, project):
    from repositories import cable_repository

    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))

    cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id, cable_type="USB")
    )
    cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id, cable_type="HDMI")
    )

    cables = cable_repository.list_by_project(conn, project.project_id)
    assert len(cables) == 2


def test_delete_equipment_cascades_cable_deletion(conn, project):
    from repositories import cable_repository, equipment_repository

    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))
    cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )

    equipment_service.delete_equipment(conn, a.equipment_id, cascade_children=False)

    assert cable_repository.list_by_project(conn, project.project_id) == []
