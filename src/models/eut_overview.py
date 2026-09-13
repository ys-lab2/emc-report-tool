from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Frequency:
    frequency_id: str
    eut_overview_id: str
    value: str = ""
    unit: str = ""
    usage_note: str = ""
    sort_order: int = 0


@dataclass
class EutOverview:
    eut_overview_id: str
    project_id: str
    kind_of_equipment: str = ""
    model_name: str = ""
    serial_no: str = ""
    operating_program: str = ""
    sample_type: str = ""  # "mass_production" or "pre_production"
    width_mm: float | None = None
    depth_mm: float | None = None
    height_mm: float | None = None
    max_frequency: str = ""
    wireless_frequency: str = ""
    rating_power_supply_types: list[str] = field(default_factory=list)
    rating_power_supply_value: str = ""
    tested_condition: str = ""
    date_of_manufacture: str = ""
    manufacturer_name: str = ""
    manufacturer_address: str = ""
    attachment: str = ""
    option: str = ""
    date_sample_received: str = ""
    test_engineer: str = ""
