from models.cable import Cable
from models.equipment import Equipment
from models.ground_connection import GroundConnection
from models.inline_component import InlineComponent
from models.power_source import PowerSource
from repositories import diagram_repository
from services import (
    cable_service,
    equipment_service,
    ground_connection_service,
    inline_component_service,
    power_source_service,
)
from diagram.layout import auto_layout


def make_equipment(project_id, display_id, parent_id=None, placement_type="standalone", category="EUT"):
    return Equipment(
        equipment_id="",
        project_id=project_id,
        display_id=display_id,
        category=category,
        parent_equipment_id=parent_id,
        placement_type=placement_type,
    )


def test_creating_equipment_creates_diagram_node(conn, project):
    equipment = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))

    node = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", equipment.equipment_id)
    assert node is not None
    assert node.parent_node_id is None


def test_child_equipment_gets_node_with_parent_link(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )

    node_a = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", a.equipment_id)
    node_b = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", b.equipment_id)

    assert node_b.parent_node_id == node_a.node_id


def test_deleting_equipment_removes_diagram_node(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    equipment_service.delete_equipment(conn, a.equipment_id, cascade_children=False)

    node = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", a.equipment_id)
    assert node is None


def test_creating_cable_creates_diagram_edge(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))
    cable = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )

    edge = diagram_repository.get_edge_by_ref(conn, project.project_id, "Cable", cable.cable_id)
    assert edge is not None


def test_deleting_cable_removes_diagram_edge(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))
    cable = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )

    cable_service.delete_cable(conn, cable.cable_id)

    edge = diagram_repository.get_edge_by_ref(conn, project.project_id, "Cable", cable.cable_id)
    assert edge is None


def test_power_source_and_ground_get_nodes(conn, project):
    power = power_source_service.create_power_source(
        conn, PowerSource(power_source_id="", project_id=project.project_id, kind="ACPowerSupply")
    )
    ground = ground_connection_service.create_ground_connection(
        conn, GroundConnection(ground_connection_id="", project_id=project.project_id, kind="FG")
    )

    power_node = diagram_repository.get_node_by_ref(conn, project.project_id, "PowerSource", power.power_source_id)
    ground_node = diagram_repository.get_node_by_ref(conn, project.project_id, "GroundConnection", ground.ground_connection_id)

    assert power_node is not None
    assert ground_node is not None

    power_source_service.delete_power_source(conn, power.power_source_id)
    assert diagram_repository.get_node_by_ref(conn, project.project_id, "PowerSource", power.power_source_id) is None


def test_inline_component_crud(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(conn, make_equipment(project.project_id, "B"))
    cable = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_ref_id=a.equipment_id, to_ref_id=b.equipment_id)
    )

    component = inline_component_service.add_component(
        conn,
        InlineComponent(inline_component_id="", cable_id=cable.cable_id, type="FerriteCore", model="ZCAT2035-0930"),
    )
    items = inline_component_service.list_for_cable(conn, cable.cable_id)
    assert len(items) == 1
    assert items[0].model == "ZCAT2035-0930"

    component.manufacturer = "TDK"
    inline_component_service.update_component(conn, component)
    items = inline_component_service.list_for_cable(conn, cable.cable_id)
    assert items[0].manufacturer == "TDK"

    inline_component_service.delete_component(conn, component.inline_component_id)
    assert inline_component_service.list_for_cable(conn, cable.cable_id) == []


def test_auto_layout_positions_by_category(conn, project):
    eut = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A", category="EUT"))
    peripheral = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", category="Peripheral")
    )
    associated = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "C", category="AssociatedEquipment")
    )

    auto_layout.layout_all(conn, project.project_id)

    node_eut = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", eut.equipment_id)
    node_peripheral = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", peripheral.equipment_id)
    node_associated = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", associated.equipment_id)

    assert node_peripheral.x < node_eut.x < node_associated.x


def test_auto_layout_keeps_children_within_parent_bounds(conn, project):
    a = equipment_service.create_equipment(conn, make_equipment(project.project_id, "A"))
    b = equipment_service.create_equipment(
        conn, make_equipment(project.project_id, "B", parent_id=a.equipment_id, placement_type="embedded")
    )

    auto_layout.layout_all(conn, project.project_id)

    node_a = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", a.equipment_id)
    node_b = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", b.equipment_id)

    assert 0 <= node_b.relative_x <= node_a.width
    assert 0 <= node_b.relative_y <= node_a.height
