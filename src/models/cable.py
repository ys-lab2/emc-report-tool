from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Cable:
    cable_id: str
    project_id: str
    cable_no: int = 0
    from_equipment_id: str = ""
    from_port: str = ""
    to_equipment_id: str = ""
    to_port: str = ""
    cable_type: str = ""
    length: float | None = None
    length_unit: str = "m"
    shielded: str = "unknown"  # "shielded" / "non_shielded" / "unknown"
    maximum_length: str = ""
    outdoor_connection: str = "unknown"  # "yes" / "no" / "unknown"
    notes: str = ""
    sort_order: int = 0
    created_at: str = ""
    updated_at: str = ""
