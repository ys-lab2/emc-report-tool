import pytest

from services import project_service


def test_create_new_and_reopen(tmp_path):
    file_path = tmp_path / "PJ260001.emcproj"

    handle = project_service.create_new(file_path)
    handle.project.project_no = "PJ260001"
    project_service.save(handle)
    handle.close()

    reopened = project_service.open_project(file_path)
    assert reopened.project.project_no == "PJ260001"
    reopened.close()


def test_create_new_rejects_existing_file(tmp_path):
    file_path = tmp_path / "PJ260002.emcproj"
    file_path.write_text("dummy")

    with pytest.raises(FileExistsError):
        project_service.create_new(file_path)


def test_open_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        project_service.open_project(tmp_path / "does_not_exist.emcproj")


def test_save_as_copies_to_new_path(tmp_path):
    original_path = tmp_path / "PJ260003.emcproj"
    new_path = tmp_path / "PJ260003_copy.emcproj"

    handle = project_service.create_new(original_path)
    handle.project.project_no = "PJ260003"
    project_service.save(handle)

    new_handle = project_service.save_as(handle, new_path)

    assert new_path.exists()
    assert new_handle.project.project_no == "PJ260003"
    new_handle.close()
