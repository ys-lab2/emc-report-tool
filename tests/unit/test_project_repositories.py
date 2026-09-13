from models.applicant import Applicant
from models.eut_overview import EutOverview, Frequency
from models.report_standard import ReportStandard
from repositories import applicant_repository, eut_overview_repository, report_standard_repository


def test_project_round_trip(conn, project):
    from repositories import project_repository

    project.project_no = "PJ260001"
    project.test_plan_no = "TP-001"
    project_repository.update(conn, project)

    reloaded = project_repository.get(conn, project.project_id)
    assert reloaded.project_no == "PJ260001"
    assert reloaded.test_plan_no == "TP-001"


def test_applicant_upsert_is_one_to_one(conn, project):
    a = Applicant(applicant_id="", project_id=project.project_id, company_name_jp="株式会社テスト")
    saved = applicant_repository.upsert(conn, a)
    assert saved.applicant_id

    saved.company_name_en = "Test Co., Ltd."
    applicant_repository.upsert(conn, saved)

    reloaded = applicant_repository.get_by_project(conn, project.project_id)
    assert reloaded.company_name_jp == "株式会社テスト"
    assert reloaded.company_name_en == "Test Co., Ltd."
    assert reloaded.applicant_id == saved.applicant_id


def test_report_standard_crud(conn, project):
    s = ReportStandard(report_standard_id="", project_id=project.project_id, standard_name="CISPR 32")
    added = report_standard_repository.add(conn, s)

    items = report_standard_repository.list_by_project(conn, project.project_id)
    assert len(items) == 1
    assert items[0].standard_name == "CISPR 32"

    added.standard_name = "CISPR 35"
    report_standard_repository.update(conn, added)
    items = report_standard_repository.list_by_project(conn, project.project_id)
    assert items[0].standard_name == "CISPR 35"

    report_standard_repository.delete(conn, added.report_standard_id)
    assert report_standard_repository.list_by_project(conn, project.project_id) == []


def test_eut_overview_upsert_and_frequencies(conn, project):
    overview = EutOverview(
        eut_overview_id="",
        project_id=project.project_id,
        model_name="ABC-100",
        rating_power_supply_types=["dc_2p", "single_phase_2p"],
    )
    saved = eut_overview_repository.upsert(conn, overview)

    reloaded = eut_overview_repository.get_by_project(conn, project.project_id)
    assert reloaded.model_name == "ABC-100"
    assert reloaded.rating_power_supply_types == ["dc_2p", "single_phase_2p"]

    freq = Frequency(frequency_id="", eut_overview_id=saved.eut_overview_id, value="2.4", unit="GHz")
    eut_overview_repository.add_frequency(conn, freq)
    freqs = eut_overview_repository.list_frequencies(conn, saved.eut_overview_id)
    assert len(freqs) == 1
    assert freqs[0].value == "2.4"

    eut_overview_repository.delete_frequency(conn, freqs[0].frequency_id)
    assert eut_overview_repository.list_frequencies(conn, saved.eut_overview_id) == []
