from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path

import pythoncom
import win32com.client


@contextmanager
def word_application(visible: bool = False):
    """Word COMアプリケーションのライフサイクルを管理する。
    例外発生時も確実にWordプロセスを終了させ、ゾンビプロセスを残さない（48.節・60.節）。
    このスレッドでCOMが未初期化の場合に備えCoInitializeを呼ぶ（同一スレッド内で複数回
    呼んでも安全）。ただしCoUninitializeは呼ばない：呼び出し元（GUIやテストコードなど）が
    同じスレッドで別途COM操作を続ける可能性があり、ここで解放すると以後のCOM呼び出しが
    「CoInitializeが呼び出されていません」エラーで失敗するようになるため。"""
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = visible
    try:
        yield word
    finally:
        word.Quit()


def copy_template(template_path: Path, output_path: Path) -> Path:
    """テンプレートをコピーしてから編集する（7.節：テンプレートを直接編集しない）。"""
    if output_path.exists():
        raise FileExistsError(f"すでにファイルが存在します: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, output_path)
    return output_path


def set_cell_text(table, row: int, col: int, text: str) -> None:
    """セルの内容を完全に置き換える。空欄セル（記入例が無いもの）への書き込み専用。"""
    cell = table.Cell(row, col)
    cell.Range.Text = text or ""


def append_cell_text(table, row: int, col: int, text: str) -> None:
    """既存のガイド文・記入例を残したまま、セル末尾に改行して追記する。
    テンプレートの案内文を上書きで壊さないための安全策（word-template-analysis.md 9A.節）。"""
    if not text:
        return
    cell = table.Cell(row, col)
    end_range = cell.Range
    end_range.Collapse(0)  # wdCollapseEnd
    end_range.MoveEnd(1, -1)  # 末尾のセル区切り文字の直前まで戻る (wdCharacter)
    end_range.InsertAfter(f"\n{text}")


def set_checkbox(doc, index_1based: int, checked: bool) -> None:
    """ContentControls(index)のチェックボックス状態を設定する。
    テンプレートにタグ名が無いため出現順インデックスに依存する
    （word-template-analysis.md 5.節：テンプレート変更に弱い箇所として明記済み）。"""
    doc.ContentControls(index_1based).Checked = checked


def insert_picture_replacing_cell(table, row: int, col: int, image_path: Path) -> None:
    """セルの内容（記入例画像やプレースホルダ文字列）を消して、生成した構成図画像に差し替える。"""
    cell = table.Cell(row, col)
    cell.Range.Text = ""
    cell.Range.InlineShapes.AddPicture(FileName=str(image_path))


def replace_cell_with_table(doc, table, row: int, col: int, num_rows: int, num_cols: int):
    """セルの中身（旧テンプレートの入れ子表・プレースホルダ文字列を含む）を完全に削除し、
    新しい入れ子表をゼロから作り直す。

    このテンプレートのF)寸法・G)周波数のようなセルは、見た目上は単なるラベル付きテキストに
    見えても実際には入れ子のWord表（1行複数列）が入っている。`cell.Range.Text = ""` では
    入れ子表の先頭セルしか消えず、残りのセルが残留してしまうため、必ず`cell.Tables`から
    既存の入れ子表を`Delete()`してから作り直す。

    また `doc.Tables.Add(range, num_rows, num_cols)` はこの入れ子コンテキストでは
    行数指定が無視され1行しか作られないことを実機で確認済みのため、1行×num_colsで作成した後
    `Rows.Add()`をnum_rows-1回呼んで行数を増やす。"""
    cell = table.Cell(row, col)
    while cell.Tables.Count > 0:
        cell.Tables(1).Delete()
    cell.Range.Text = ""

    nested = doc.Tables.Add(cell.Range, 1, num_cols)
    for _ in range(num_rows - 1):
        nested.Rows.Add()
    return nested


def ensure_row_capacity(table, start_row: int, fixed_capacity: int, needed_count: int) -> int:
    """機器表・ケーブル表のようにテンプレートが固定行数で用意されている表に対し、
    実際のデータ件数がそれを超える場合は行を追加する（13.節）。
    戻り値：追加した行数。呼び出し側は以降のセクションのstart_rowにこれを加算する必要がある。

    次の見出し行（供試装置/EUTのような結合済み1列セル）をBeforeRowにして
    Rows.Addすると、新しい行が見出し行側の結合書式を引き継いでしまい6列構造が壊れる。
    そのため、区分の最終データ行を選択してから Selection.InsertRowsBelow を使い、
    データ行側の書式（列構成）を確実に引き継がせる。"""
    extra = max(0, needed_count - fixed_capacity)
    if extra == 0:
        return 0

    last_data_row_index = start_row + fixed_capacity - 1
    reference_row = table.Rows(last_data_row_index)
    reference_row.Range.Select()
    table.Application.Selection.InsertRowsBelow(extra)
    return extra
