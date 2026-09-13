from models.countermeasure import Countermeasure
from models.operation_mode import OperationMode
from models.taiwan import InternalComponent
from repositories import (
    countermeasure_repository,
    immunity_repository,
    medical_repository,
    operation_mode_repository,
    taiwan_repository,
)


def test_operation_mode_crud(conn, project):
    mode = operation_mode_repository.add(
        conn, OperationMode(operation_mode_id="", project_id=project.project_id, mode_name="通常動作", description="通常時の動作説明")
    )
    items = operation_mode_repository.list_by_project(conn, project.project_id)
    assert len(items) == 1
    assert items[0].description == "通常時の動作説明"

    mode.description = "更新後の説明"
    operation_mode_repository.update(conn, mode)
    items = operation_mode_repository.list_by_project(conn, project.project_id)
    assert items[0].description == "更新後の説明"

    operation_mode_repository.delete(conn, mode.operation_mode_id)
    assert operation_mode_repository.list_by_project(conn, project.project_id) == []


def test_countermeasure_crud(conn, project):
    item = countermeasure_repository.add(
        conn,
        Countermeasure(
            countermeasure_id="", project_id=project.project_id,
            description="LANケーブルEUT側にフェライトコア追加",
            component_model="ZCAT2035-0930", component_manufacturer="TDK",
        ),
    )
    items = countermeasure_repository.list_by_project(conn, project.project_id)
    assert len(items) == 1
    assert items[0].component_manufacturer == "TDK"

    countermeasure_repository.delete(conn, item.countermeasure_id)
    assert countermeasure_repository.list_by_project(conn, project.project_id) == []


def test_immunity_criteria_get_or_create_and_verification_points(conn, project):
    criteria = immunity_repository.get_or_create(conn, project.project_id)
    criteria2 = immunity_repository.get_or_create(conn, project.project_id)
    assert criteria.immunity_criteria_id == criteria2.immunity_criteria_id

    criteria.criterion_a = "通常動作を継続すること"
    immunity_repository.update(conn, criteria)
    reloaded = immunity_repository.get_by_project(conn, project.project_id)
    assert reloaded.criterion_a == "通常動作を継続すること"

    immunity_repository.replace_verification_points(conn, criteria.immunity_criteria_id, ["表示確認", "音声確認", "通信確認"])
    points = immunity_repository.list_verification_points(conn, criteria.immunity_criteria_id)
    assert [p.content for p in points] == ["表示確認", "音声確認", "通信確認"]

    immunity_repository.replace_verification_points(conn, criteria.immunity_criteria_id, ["表示確認のみ"])
    points = immunity_repository.list_verification_points(conn, criteria.immunity_criteria_id)
    assert [p.content for p in points] == ["表示確認のみ"]


def test_medical_criteria_get_or_create_and_items(conn, project):
    criteria = medical_repository.get_or_create(conn, project.project_id)
    criteria.immunity_performance_text = "性能基準の説明文"
    medical_repository.update(conn, criteria)

    medical_repository.replace_items(conn, criteria.medical_criteria_id, "basic_safety", ["感電しないこと", "発火しないこと"])
    medical_repository.replace_items(conn, criteria.medical_criteria_id, "basic_performance", ["測定精度を維持すること"])

    safety_items = medical_repository.list_items(conn, criteria.medical_criteria_id, "basic_safety")
    performance_items = medical_repository.list_items(conn, criteria.medical_criteria_id, "basic_performance")

    assert [i.content for i in safety_items] == ["感電しないこと", "発火しないこと"]
    assert [i.content for i in performance_items] == ["測定精度を維持すること"]

    reloaded = medical_repository.get_by_project(conn, project.project_id)
    assert reloaded.immunity_performance_text == "性能基準の説明文"


def test_taiwan_applicant_get_or_create_and_internal_components(conn, project):
    applicant = taiwan_repository.get_or_create(conn, project.project_id)
    applicant.company_name_en = "Sample Co., Ltd."
    applicant.eut_operation_status_text = "電源投入後、自動的に測定モードへ移行する。"
    taiwan_repository.update(conn, applicant)

    reloaded = taiwan_repository.get_by_project(conn, project.project_id)
    assert reloaded.company_name_en == "Sample Co., Ltd."
    assert reloaded.eut_operation_status_text.startswith("電源投入後")

    component = taiwan_repository.add_internal_component(
        conn,
        InternalComponent(
            internal_component_id="", taiwan_applicant_id=applicant.taiwan_applicant_id,
            device_name="CPU", quantity_max="1", model_name="ABCxxx", manufacturer="Intel",
        ),
    )
    components = taiwan_repository.list_internal_components(conn, applicant.taiwan_applicant_id)
    assert len(components) == 1
    assert components[0].device_name == "CPU"

    component.manufacturer = "AMD"
    taiwan_repository.update_internal_component(conn, component)
    components = taiwan_repository.list_internal_components(conn, applicant.taiwan_applicant_id)
    assert components[0].manufacturer == "AMD"

    taiwan_repository.delete_internal_component(conn, component.internal_component_id)
    assert taiwan_repository.list_internal_components(conn, applicant.taiwan_applicant_id) == []
