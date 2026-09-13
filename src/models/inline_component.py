from __future__ import annotations

from dataclasses import dataclass

INLINE_COMPONENT_TYPES = (
    "FerriteCore",
    "ClampFilter",
    "CommonModeFilter",
    "Filter",
    "Attenuator",
    "Adapter",
    "Other",
)
POSITIONS = ("FromSide", "Middle", "ToSide")


@dataclass
class InlineComponent:
    inline_component_id: str
    cable_id: str
    type: str = "FerriteCore"
    name: str = ""
    model: str = ""
    manufacturer: str = ""
    quantity: int = 1
    position: str = "Middle"
    notes: str = ""
    countermeasure_id: str | None = None
    sort_order: int = 0
