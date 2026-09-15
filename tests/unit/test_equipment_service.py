import pytest

from models.cable import Cable
from models.equipment import Equipment
from services import cable_service, equipment_service
from services.equipment_service import CircularContainmentError


def make_equipment(project_id, display_id, parent_id=None, placement_type="standalone"):
    return Equipment(
        equipment_id="",
        project_id=project_id,
        display_id=display_id,
        category="EUT",
        parent_equipment_id=parent_id,
        placement_type=placement_type,
    )


def test_create_equipment_assigns_id(conn, project):
    e = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    assert e.equipment_id


def test_self_parent_rejected(conn, project):
    e = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    e.parent_equipment_id = e.equipment_id
    with pytest.raises(CircularContainmentError):
        equipment_service.update_equipment(conn, e)


def test_multi_level_cycle_rejected(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )
    c = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "C", parent_id=b.equipment_id, placement_type="embedded")
    )

    # A -> B -> C が既に成立している状態で、A の親を C にしようとすると循環になる
    a.parent_equipment_id = c.equipment_id
    with pytest.raises(CircularContainmentError):
        equipment_service.update_equipment(conn, a)


def test_valid_multi_level_containment_allowed(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )
    c = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "C", parent_id=b.equipment_id, placement_type="embedded")
    )
    assert c.parent_equipment_id == b.equipment_id
    assert b.parent_equipment_id == a.equipment_id


def test_deletion_impact_reports_cables_and_children(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )
    c = equipment_service.create_equipment(conn, make_equipment(project.project_id, "C"))
    cable_service.create_cable(
        conn,
        Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=c.equipment_id),
    )

    impact = equipment_service.get_deletion_impact(conn, a.equipment_id)
    assert impact.referencing_cable_count == 1
    assert len(impact.direct_children) == 1
    assert impact.direct_children[0].equipment_id == b.equipment_id
    assert impact.has_warnings is True


def test_delete_equipment_without_cascade_frees_children(conn, project):
    from repositories import equipment_repository

    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )

    equipment_service.delete_equipment(conn, a.equipment_id, cascade_children=False)

    reloaded_b = equipment_repository.get(conn, b.equipment_id)
    assert reloaded_b is not None
    assert reloaded_b.parent_equipment_id is None
    assert reloaded_b.placement_type == "standalone"
    assert equipment_repository.get(conn, a.equipment_id) is None


def test_delete_equipment_with_cascade_removes_children(conn, project):
    from repositories import equipment_repository

    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )

    equipment_service.delete_equipment(conn, a.equipment_id, cascade_children=True)

    assert equipment_repository.get(conn, a.equipment_id) is None
    assert equipment_repository.get(conn, b.equipment_id) is None


def test_next_display_id_sequence(conn, project):
    assert equipment_service.next_display_id(conn, project.project_id) == "A"
    equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    assert equipment_service.next_display_id(conn, project.project_id) == "B"
