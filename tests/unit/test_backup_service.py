import time

from services import backup_service, project_service


def test_create_backup_copies_file(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backup"
    monkeypatch.setattr(backup_service, "BACKUP_DIR", backup_dir)

    project_path = tmp_path / "PJ260001.emcproj"
    handle = project_service.create_new(project_path)

    backup_path = backup_service.create_backup(handle, generations=5)

    assert backup_path.exists()
    assert backup_path.parent == backup_dir
    handle.close()


def test_create_backup_prunes_old_generations(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backup"
    monkeypatch.setattr(backup_service, "BACKUP_DIR", backup_dir)

    project_path = tmp_path / "PJ260002.emcproj"
    handle = project_service.create_new(project_path)

    for _ in range(5):
        backup_service.create_backup(handle, generations=3)
        time.sleep(0.01)

    remaining = list(backup_dir.glob("PJ260002_*.emcproj"))
    assert len(remaining) == 3
    handle.close()
