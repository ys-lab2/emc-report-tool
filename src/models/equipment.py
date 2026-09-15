from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = ("EUT", "Peripheral", "AssociatedEquipment", "Other")
PLACEMENT_TYPES = ("standalone", "embedded", "inserted", "attached")


@dataclass
class Equipment:
    equipment_id: str
    project_id: str
    display_id: str = ""
    category: str = "EUT"
    description: str = ""
    model_name: str = ""
    serial: str = ""
    manufacturer: str = ""
    fcc_id: str = ""
    bsmi_id: str = ""
    notes: str = ""
    placement_type: str = "standalone"
    parent_equipment_id: str | None = None
    width_mm: float | None = None
    depth_mm: float | None = None
    height_mm: float | None = None
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""
