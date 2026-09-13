# 開発計画

指示書66.節のPhase構成を、実装単位まで細分化する。各Phaseは「1機能→実装→テスト→報告→承認→次へ」（77.節/実装方針）の順で小さく進める。承認までコード実装（Phase 0以降）を開始しない。

## Phase 0：設計・基盤

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 0-1 | 設計ドキュメント確定 | `docs/*.md` | 本セッションで作成した6文書をユーザーがレビュー・承認 | - | ユーザー承認 |
| 0-2 | プロジェクト雛形 | `pyproject.toml`/`requirements.txt`, `src/app.py` | Python環境、依存パッケージ定義、PySide6起動のみの空アプリ | `python src/app.py`でウィンドウが開くことを確認 | 空ウィンドウ起動 |
| 0-3 | ログ基盤 | `src/logging_setup.py` | `logs/app.log`へのローテーティングファイルハンドラ設定 | ログ出力の単体テスト | エラー時にログが記録される |
| 0-4 | DB接続基盤 | `src/database/connection.py`, `migrations/0001_initial.sql` | `database-schema.md`のDDLを適用するマイグレーション機構 | 新規DB作成→全テーブル存在確認のテスト | マイグレーションが冪等に動く |
| 0-5 | 設定ファイル | `src/config.py` | 自動保存間隔・最近使用プロジェクト等の設定読み書き | 設定読み書きの単体テスト | 設定の永続化確認 |

## Phase 1：プロジェクトと基本入力

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 1-1 | Project CRUD | `repositories/project_repository.py`, `services/project_service.py` | 新規作成/保存/開く/名前を付けて保存 | Repository単体テスト、Service経由の保存→再読込一致テスト | 保存→再読込でデータ一致 |
| 1-2 | プロジェクト基本情報画面 | `ui/pages/project_page.py` | プロジェクト番号・テストプラン番号・測定期間・レポート作成規格の入力 | 手動UI確認 | 入力→保存→再読込で値が復元される |
| 1-3 | 申請者画面 | `ui/pages/applicant_page.py`, `repositories/applicant_repository` | Applicant CRUD | 同上 | 同上 |
| 1-4 | 装置概要画面 | `ui/pages/eut_overview_page.py` | EutOverview全項目、チェックボックス群（sample_type, rating_power_supply） | 同上 | 同上 |
| 1-5 | Equipment CRUD + Containment | `services/equipment_service.py`, `ui/pages/equipment_list_page.py`, `ui/dialogs/equipment_edit_dialog.py` | 3.1/3.2節のUI、循環参照チェック | 循環参照禁止の単体テスト（A→B→A禁止、A→A禁止）、多段階（A→B→C）許可テスト | 不正な親子設定が拒否される |
| 1-6 | Cable CRUD | `services/cable_service.py`, `ui/pages/cable_list_page.py` | 4.節のインライン編集グリッド | From/To未設定時の警告、存在しないEquipment参照の拒否テスト | ケーブル入力→保存→再読込一致 |
| 1-7 | 最近使用したプロジェクト・自動保存・バックアップ | `services/backup_service.py` | 起動時最近使用リスト表示、一定間隔自動保存、`backup/`世代保存 | 自動保存タイマーの単体テスト | 異常終了想定シナリオでバックアップから復元できる |

## Phase 2：Connection・構成図

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 2-1 | InlineComponent | `services/`, `ui/` | ケーブル明細へのフェライト等追加UI | CRUD単体テスト | 複数InlineComponent登録・削除確認 |
| 2-2 | PowerSource / GroundConnection | 同上 | 電源・GND登録UI（構成図用の最小属性のみ） | CRUD単体テスト | 登録・削除確認 |
| 2-3 | DiagramNode基盤 | `diagram/scene.py`, `diagram/items/equipment_item.py` | QGraphicsSceneへのNode描画、Equipment⇔DiagramNode同期 | 座標保存→再読込一致テスト | 図を保存し再度開いて同一表示になる |
| 2-4 | Equipment親子のQt Item表現 | `diagram/items/` | `setParentItem`でContainmentを表現、親移動で子が追従 | 手動UI確認＋座標計算の単体テスト | 親移動時、子の相対位置が保たれる |
| 2-5 | DiagramEdge（Cable線） | `diagram/items/cable_item.py` | 直線/折れ線描画、ラベル表示 | 手動UI確認 | ケーブル追加が線として表示される |
| 2-6 | 構成図編集操作 + Undo/Redo | `diagram/commands/` | Move/Resize/Add/Delete/LabelMoveの`QUndoCommand`化 | 各コマンドのUndo/Redo単体テスト | 全操作がUndo/Redoできる |
| 2-7 | 自動配置 | `diagram/layout/auto_layout.py` | 32.節ルールの初期配置アルゴリズム | 配置結果のスナップショットテスト | カテゴリ別に妥当な位置へ配置される |
| 2-8 | 構成図保存・再現 | `repositories/diagram_repository.py` | DiagramNode/DiagramEdgeの永続化 | 保存→再読込→ピクセル座標一致テスト | 33.節の要件（完全再現）を満たす |

## Phase 3：Word出力

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 3-1 | テンプレート前処理ツール | `tools/inspect_template.py` | 新規テンプレート受領時に自動解析するスクリプト（本セッションのanalyze_docx.py相当を正式化） | テンプレートに対して実行しエラー無く解析結果が出る | 任意のdocxに対して構造レポートが出力される |
| 3-2 | Word Exporter基盤 | `exporters/word/base.py`, `registry.py` | Word COM起動・終了の共通処理、テンプレートコピー→別名保存の基本フロー | Integration Test（Word必須環境でのみ実行） | テンプレートコピーが別名で保存される |
| 3-3 | 基本情報・装置概要の出力 | `exporters/word/fm05_v36.py` | Table0/2/3への書き込み、チェックボックス設定（word-template-analysis.md 3節のインデックス対応） | Integration Test：出力後のdocxを再度python-docxで開き値を検証 | 主要項目がテンプレート通りの位置に出力される |
| 3-4 | 機器表・ケーブル表の出力（行複製対応） | 同上 | Table4/5への行複製ロジック | 行数超過時の複製動作テスト | 15台の機器でも正しく出力される |
| 3-5 | 構成図画像の出力 | `diagram/renderer/svg_renderer.py`, Exporter連携 | オフスクリーンレンダリング→画像化→Table7セルへ挿入 | 画像生成の単体テスト＋Integration Test | 構成図が画面表示と同じ内容でWordに挿入される |

## Phase 4：資料全体対応

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 4-1 | EMC対策画面・出力 | `ui/pages/countermeasure_page.py`, Exporter追加 | Table8対応 | Integration Test | 対策内容が出力される |
| 4-2 | イミュニティ画面・出力 | `ui/pages/immunity_page.py` | Table9対応、動作確認箇所の可変行 | 同上 | 追加資料Aが出力される |
| 4-3 | 医療規格画面・出力 | `ui/pages/medical_page.py` | Table10対応 | 同上 | 追加資料Bが出力される |
| 4-4 | 台湾資料画面・出力 | `ui/pages/taiwan_page.py` | Table13対応、内部構成品リストの可変行 | 同上 | 追加資料Dが出力される |
| 4-5 | 追加資料選択フラグ | `ui/`, Exporter | 38.節の☑Immunity/Medical/Taiwan制御 | 出力要否の分岐テスト | フラグに応じてページ出力が切り替わる |

## Phase 5：出力拡張

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 5-1 | PDF出力 | `exporters/pdf/pdf_exporter.py` | `ExportAsFixedFormat`によるWord→PDF変換 | Integration Test | WordとPDFの見た目が一致 |
| 5-2 | Excel出力 | `exporters/excel/workbook_exporter.py` | 基本情報/機器/ケーブル/構成図画像貼付シート | 単体テスト（openpyxl出力内容検証） | 4シートが正しく生成される |

## Phase 6：顧客資料インポート（Excel/Word/デジタルPDF）

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 6-1 | Excelインポート | `importers/excel_importer.py`, `mapping/field_mapping.py` | 40.節のマッピング辞書によるセル→候補変換 | サンプルExcelでの単体テスト | 候補リストが正しく生成される |
| 6-2 | Wordインポート | `importers/word_importer.py` | 表構造解析、機器表/ケーブル表/その他の分類候補提示 | サンプルWordでの単体テスト | 分類候補が提示される（自動確定しない） |
| 6-3 | デジタルPDFインポート | `importers/pdf_importer.py` | PyMuPDFによるテキスト・表抽出 | サンプルPDFでの単体テスト | テキストが抽出される |
| 6-4 | Import確認画面 | `ui/dialogs/import_review_dialog.py` | 45.節のUI、信頼度表示 | 手動UI確認 | 確認・修正・取り込みが正常動作 |
| 6-5 | ImportProfile | `importers/mapping/import_profile.py`, 別設定DB | 47.節の顧客別マッピング保存・適用 | 単体テスト | プロファイル選択で自動マッピングされる |

## Phase 7：画像・OCR

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 7-1 | 画像インポート基盤 | `importers/image_importer.py` | PNG/JPEG読込、前処理（Pillow/OpenCV） | 単体テスト | 画像読込・前処理が動く |
| 7-2 | ローカルOCR統合 | 同上 | OCRエンジン連携（完全ローカル、5.節のセキュリティ要件遵守） | サンプル画像でのOCR結果テスト | テキストが抽出される |
| 7-3 | スキャンPDFフォールバック | `importers/pdf_importer.py` | デジタルPDF抽出失敗時のOCR切替 | 単体テスト | スキャンPDFでも候補が出る |

## Phase 8：構成図認識（将来検討・実験的機能）

| Task | 目的 | 変更ファイル | 実装内容 | テスト内容 | 完了条件 |
|---|---|---|---|---|---|
| 8-1 | 構成図認識の検証 | `importers/image_importer.py`拡張 | 矩形/線/記号検出の実験実装 | 精度検証（誤認識率の計測） | 候補としてのみ提示、直接登録しない設計を維持 |

Phase 8は誤認識リスクが高い（44.節）ため、他Phaseと異なり「実用化を急がない検証Phase」として扱う。着手前に改めてユーザーと相談する。

## 進め方の運用ルール

1. 各Task完了ごとに、対象の自動テストを実行し結果を報告する。
2. UIを伴うTaskは、可能な範囲でアプリを実際に起動して動作確認したスクリーンショットまたは手順を報告する。
3. 既存機能に影響するTask（特にDBスキーマ変更を伴うもの）は、着手前に影響範囲（どのRepository/Service/Exporterが変更対象か）を明示してから着手する。
4. スキーマ変更を伴う場合は`database-schema.md` 15.節の互換性ルールに従い、必ずマイグレーションファイルを追加する形で対応する。
5. Word COM・OCR等、環境依存で自動テストが困難な部分は、Integration Testとして明示的に分離し、可能な範囲のみを自動化する。

## MVP完成条件（67.節の再掲・Phase対応表）

| MVP要件 | 対応Phase/Task |
|---|---|
| 新規プロジェクト/保存/読込 | 1-1 |
| 基本情報入力 | 1-2, 1-3, 1-4 |
| Equipment入力・親子関係設定 | 1-5 |
| Cable入力・Connection入力 | 1-6 |
| 構成図自動生成・内包表示・手動調整・再読込再現 | 2-3〜2-8 |
| 既存Wordテンプレートへ出力 | 3-1〜3-5 |
| WordからPDF出力 | 5-1 |

Phase 0〜3および5-1が完了した時点でMVPとみなし、そこでユーザーへ中間報告・実運用試用を依頼する。
