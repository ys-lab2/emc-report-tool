from __future__ import annotations

from exporters.word import fm05_v36

_EXPORTERS = {
    (fm05_v36.TEMPLATE_ID, fm05_v36.TEMPLATE_VERSION): fm05_v36,
}


class UnknownTemplateError(Exception):
    """未知のテンプレートID・バージョンに対するExporterが見つからない場合の例外（8.節）。
    互換性がありそうでも安易に近いバージョンで代用しない。"""


def resolve_exporter(template_id: str, template_version: str):
    key = (template_id, template_version)
    exporter = _EXPORTERS.get(key)
    if exporter is None:
        raise UnknownTemplateError(
            f"テンプレート '{template_id}' バージョン '{template_version}' に対応するExporterがありません。"
        )
    return exporter
