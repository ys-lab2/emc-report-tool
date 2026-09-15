from __future__ import annotations

from dataclasses import dataclass

REF_TYPES = ("Equipment", "PowerSource", "GroundConnection")


@dataclass
class Cable:
    cable_id: str
    project_id: str
    cable_no: int = 0
    from_ref_type: str = "Equipment"
    from_ref_id: str = ""
    from_port: str = ""
    to_ref_type: str = "Equipment"
    to_ref_id: str = ""
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
