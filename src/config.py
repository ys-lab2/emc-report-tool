from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_DIR_NAME = "EmcReportTool"
DEFAULT_AUTOSAVE_INTERVAL_SECONDS = 300
DEFAULT_BACKUP_GENERATIONS = 5
DEFAULT_FONT_FAMILY = "Times New Roman"
DEFAULT_FONT_SIZE = 10
MAX_RECENT_PROJECTS = 10


def app_data_dir() -> Path:
    root = Path.home() / "AppData" / "Roaming"
    path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file_path() -> Path:
    return app_data_dir() / "config.json"


@dataclass
class AppConfig:
    autosave_interval_seconds: int = DEFAULT_AUTOSAVE_INTERVAL_SECONDS
    backup_generations: int = DEFAULT_BACKUP_GENERATIONS
    recent_projects: list[str] = field(default_factory=list)
    font_family: str = DEFAULT_FONT_FAMILY
    font_size: int = DEFAULT_FONT_SIZE

    def add_recent_project(self, project_path: str) -> None:
        paths = [p for p in self.recent_projects if p != project_path]
        paths.insert(0, project_path)
        self.recent_projects = paths[:MAX_RECENT_PROJECTS]


def load_config() -> AppConfig:
    path = config_file_path()
    if not path.exists():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppConfig()
    return AppConfig(
        autosave_interval_seconds=data.get(
            "autosave_interval_seconds", DEFAULT_AUTOSAVE_INTERVAL_SECONDS
        ),
        backup_generations=data.get("backup_generations", DEFAULT_BACKUP_GENERATIONS),
        recent_projects=data.get("recent_projects", []),
        font_family=data.get("font_family", DEFAULT_FONT_FAMILY),
        font_size=data.get("font_size", DEFAULT_FONT_SIZE),
    )


def save_config(config: AppConfig) -> None:
    path = config_file_path()
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8"
    )
