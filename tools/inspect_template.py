"""Wordテンプレートの構造を実際にMicrosoft Word COM経由で解析するツール。

新しいテンプレートを受け取った場合、まずこのツールを実行して
Table/Cellのアドレス可能な構造・ContentControl（チェックボックス等）の
並び順を確認してからWordExporterを実装・修正すること
（docs/word-template-analysis.md 9A.節を参照）。

使い方:
    python tools/inspect_template.py "テンプレート/xxx.docx" > report.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

import win32com.client


def inspect(template_path: Path, max_cols: int = 10) -> str:
    lines: list[str] = []
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(template_path), ReadOnly=True)
        try:
            lines.append(f"=== {template_path.name} ===")
            lines.append(f"Word Tables count (COM基準): {doc.Tables.Count}")
            lines.append(f"ContentControls count: {doc.ContentControls.Count}")

            for table_index in range(1, doc.Tables.Count + 1):
                lines.extend(_dump_table(doc, table_index, max_cols))

            lines.append("\n=== ContentControls (document order) ===")
            for i, cc in enumerate(doc.ContentControls, start=1):
                try:
                    checked = cc.Checked
                except Exception:
                    checked = None
                nearby = cc.Range.Paragraphs(1).Range.Text.strip()[:60] if cc.Range else ""
                lines.append(f"CC[{i}] type={cc.Type} checked={checked} nearby='{nearby}'")

            lines.append("\n=== Header/Footer text ===")
            section = doc.Sections(1)
            for p in section.Headers(1).Range.Paragraphs:
                text = p.Range.Text.strip()
                if text:
                    lines.append(f"header: {text}")
            for p in section.Footers(1).Range.Paragraphs:
                text = p.Range.Text.strip()
                if text:
                    lines.append(f"footer: {text}")
        finally:
            doc.Close(False)
    finally:
        word.Quit()

    return "\n".join(lines)


def _dump_table(doc, table_index: int, max_cols: int) -> list[str]:
    lines = []
    table = doc.Tables(table_index)
    n_rows = table.Rows.Count
    lines.append(f"\n===== Table {table_index}: Rows={n_rows} =====")
    for r in range(1, n_rows + 1):
        row_cells = []
        for c in range(1, max_cols + 1):
            try:
                cell = table.Cell(r, c)
                text = cell.Range.Text.replace("\r", "").replace("\x07", "").replace("\x0c", "").strip()
                row_cells.append(f"C{c}='{text[:25]}'")
            except Exception:
                row_cells.append(f"C{c}=ERR")
        lines.append(f" R{r}: " + " | ".join(row_cells))
    return lines


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tools/inspect_template.py <template.docx>")
        raise SystemExit(1)

    result = inspect(Path(sys.argv[1]))
    print(result)
