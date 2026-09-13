from __future__ import annotations

from dataclasses import dataclass

GROUND_KINDS = ("PE", "FG", "SignalGND", "ChassisGND", "Earth", "Other")


@dataclass
class GroundConnection:
    ground_connection_id: str
    project_id: str
    kind: str = "PE"
    label: str = ""
    notes: str = ""
