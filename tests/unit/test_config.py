import json

import config as config_module
from config import AppConfig, load_config, save_config


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    fake_config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "config_file_path", lambda: fake_config_path)

    cfg = AppConfig(autosave_interval_seconds=120, backup_generations=3)
    cfg.add_recent_project(r"C:\proj\PJ260001.emcproj")

    save_config(cfg)
    loaded = load_config()

    assert loaded.autosave_interval_seconds == 120
    assert loaded.backup_generations == 3
    assert loaded.recent_projects == [r"C:\proj\PJ260001.emcproj"]


def test_load_config_missing_file_returns_defaults(tmp_path, monkeypatch):
    fake_config_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(config_module, "config_file_path", lambda: fake_config_path)

    cfg = load_config()

    assert cfg.autosave_interval_seconds == 300
    assert cfg.recent_projects == []
    assert cfg.font_family == "Times New Roman"


def test_font_settings_round_trip(tmp_path, monkeypatch):
    fake_config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "config_file_path", lambda: fake_config_path)

    cfg = AppConfig(font_family="Meiryo", font_size=12)
    save_config(cfg)
    loaded = load_config()

    assert loaded.font_family == "Meiryo"
    assert loaded.font_size == 12


def test_add_recent_project_dedupes_and_caps_length():
    cfg = AppConfig()
    for i in range(15):
        cfg.add_recent_project(f"P{i}.emcproj")
    cfg.add_recent_project("P5.emcproj")

    assert len(cfg.recent_projects) == 10
    assert cfg.recent_projects[0] == "P5.emcproj"


def test_load_config_ignores_corrupt_json(tmp_path, monkeypatch):
    fake_config_path = tmp_path / "config.json"
    fake_config_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(config_module, "config_file_path", lambda: fake_config_path)

    cfg = load_config()

    assert cfg.autosave_interval_seconds == 300
