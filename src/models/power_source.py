from __future__ import annotations

from dataclasses import dataclass

POWER_SOURCE_KINDS = (
    "AC100V",
    "AC200V",
    "DC24V",
    "CommercialAC",
    "StabilizedPowerSupply",
    "ACPowerSupply",
    "DCPowerSupply",
    "Other",
)


@dataclass
class PowerSource:
    power_source_id: str
    project_id: str
    kind: str = "ACPowerSupply"
    label: str = ""
    notes: str = ""
