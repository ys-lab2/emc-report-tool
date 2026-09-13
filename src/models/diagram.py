from __future__ import annotations

from dataclasses import dataclass, field

NODE_REF_TYPES = ("Equipment", "PowerSource", "GroundConnection")
DEFAULT_NODE_WIDTH = 120.0
DEFAULT_NODE_HEIGHT = 80.0


@dataclass
class DiagramNode:
    node_id: str
    project_id: str
    ref_type: str
    ref_id: str
    parent_node_id: str | None = None
    x: float = 0.0
    y: float = 0.0
    relative_x: float = 0.0
    relative_y: float = 0.0
    width: float = DEFAULT_NODE_WIDTH
    height: float = DEFAULT_NODE_HEIGHT
    z_order: int = 0
    label_dx: float = 0.0
    label_dy: float = 0.0
    fill_color: str | None = None
    stroke_color: str | None = None


@dataclass
class DiagramEdge:
    edge_id: str
    project_id: str
    ref_type: str  # "Cable"
    ref_id: str
    route_points: list[tuple[float, float]] = field(default_factory=list)
    label_dx: float = 0.0
    label_dy: float = 0.0
    line_color: str | None = None
