from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OperationMode:
    operation_mode_id: str
    project_id: str
    mode_name: str = ""
    description: str = ""
    sort_order: int = 0
