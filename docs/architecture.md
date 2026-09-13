# アーキテクチャ設計

## 1. 設計の大前提

指示書3.の通り、**アプリ内部データを正本（Single Source of Truth）とする**。Wordファイルは常に「内部データから生成される成果物」であり、Wordを直接編集して案件データを更新する運用は想定しない。

```
入力（手入力／Excel／Word／PDF／画像インポート）
        ↓
   共通データモデル（内部正本）
        ↓
   プロジェクト保存（.emcproj = SQLite）
        ↓
   ┌─────────┬─────────┬──────────┬────────────┐
   Word出力   PDF出力    Excel出力   構成図レンダリング
```

構成図レンダリング（SVG）は独立した成果物ではなく、Word/PDF/Excelの生成過程で共有される中間成果物である（49.節・51.節）。

## 2. レイヤー構成

```
┌───────────────────────────────────────────────┐
│ UI層 (PySide6)                                  │
│  - MainWindow / 左ナビゲーション / 各編集画面      │
│  - DiagramEditor (QGraphicsView)                │
│  - Import確認ダイアログ                          │
└───────────────────────────────────────────────┘
                    │  シグナル/スロット、ViewModel経由
                    ▼
┌───────────────────────────────────────────────┐
│ Service層                                        │
│  - ProjectService, EquipmentService,            │
│    CableService, ConnectionService,             │
│    DiagramService, ImmunityService,             │
│    MedicalService, TaiwanService,               │
│    ImportService, ExportService                  │
│  - 業務ルール（循環参照チェック、削除時警告等）を集約   │
└───────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌─────────────────────┐   ┌───────────────────────────┐
│ Repository層          │   │ Importer / Exporter 層       │
│  - SQLite CRUD専任     │   │  - excel/word/pdf/image     │
│  - GUIやServiceから    │   │    importer                │
│    直接SQLを書かせない  │   │  - word/excel/pdf exporter  │
└─────────────────────┘   └───────────────────────────┘
        │                              │
        ▼                              ▼
┌─────────────────────┐   ┌───────────────────────────┐
│ Database (SQLite)     │   │ 外部ツール連携                │
│  1プロジェクト=1ファイル │   │  - Word COM (pywin32)       │
└─────────────────────┘   │  - PyMuPDF / openpyxl        │
                            │  - OCR (将来・ローカル限定)     │
                            └───────────────────────────┘
```

**禁止事項（63.節・64.節の通り）：**
- Buttonクリック → その場でSQL実行、その場でWord COM呼び出し、は禁止。
- GUIコードから直接SQL文を書かない。必ずRepository経由。
- ServiceはGUIの存在を知らない（PySide6の型に依存しない）。これによりService層は将来CLIやテストから単体で呼べる。

## 3. ディレクトリ構成

指示書62.節の構成を踏襲しつつ、責務ごとに分割する。

```
emc-report-tool/
  docs/
    architecture.md
    data-model.md
    database-schema.md
    ui-design.md
    word-template-analysis.md
    development-plan.md
  テンプレート/
    MM-QR-001_FM05_...docx        # 現在使用中の実テンプレート（コピー元）
  src/
    app.py                        # エントリポイント（QApplication起動のみ）
    config.py                     # 設定ファイル読込（保存先パス、自動保存間隔等）
    logging_setup.py              # logs/app.log 初期化

    ui/
      main_window.py
      navigation/                 # 左ナビゲーション
      pages/
        project_page.py
        applicant_page.py
        eut_overview_page.py
        operation_mode_page.py
        equipment_list_page.py
        cable_list_page.py
        connection_page.py
        diagram_page.py
        countermeasure_page.py
        immunity_page.py
        medical_page.py
        taiwan_page.py
        import_page.py
        export_page.py
      dialogs/
        import_review_dialog.py
        equipment_edit_dialog.py
        containment_conflict_dialog.py
      widgets/                    # 共通部品（テーブル編集グリッド等）

    diagram/
      scene.py                    # QGraphicsScene派生
      view.py                     # QGraphicsView派生
      items/
        equipment_item.py         # 親子Item構造 (29.節)
        cable_item.py
        power_item.py
        ground_item.py
        label_item.py
      layout/
        auto_layout.py            # 32.節の自動配置ルール
      commands/                   # QUndoCommand群 (Move/Resize/Add/Delete)
      renderer/
        svg_renderer.py           # Word/PDF/Excel共有のSVG/PNG出力 (49.節)

    models/                       # dataclass / Pydanticモデル（DBスキーマとは別、アプリ内部の値オブジェクト）
      project.py
      equipment.py
      cable.py
      connection.py
      inline_component.py
      power_source.py
      ground_connection.py
      diagram.py
      countermeasure.py
      immunity.py
      medical.py
      taiwan.py
      template.py

    database/
      connection.py                # SQLite接続・PRAGMA設定
      migrations/                  # スキーマバージョン管理（alembic的な手書きマイグレーション）
        0001_initial.sql
        0002_xxx.sql
      migration_runner.py

    repositories/
      project_repository.py
      equipment_repository.py
      cable_repository.py
      connection_repository.py
      inline_component_repository.py
      power_source_repository.py
      ground_connection_repository.py
      diagram_repository.py
      countermeasure_repository.py
      immunity_repository.py
      medical_repository.py
      taiwan_repository.py
      template_repository.py
      import_repository.py

    services/
      project_service.py
      equipment_service.py         # Containment循環参照チェック等の業務ルール
      cable_service.py
      connection_service.py
      diagram_service.py
      countermeasure_service.py
      immunity_service.py
      medical_service.py
      taiwan_service.py
      import_service.py
      export_service.py
      backup_service.py

    importers/
      base.py                      # 共通インターフェース：ImportCandidate生成
      excel_importer.py
      word_importer.py
      pdf_importer.py
      image_importer.py
      mapping/
        field_mapping.py           # 40.節の項目名マッピング辞書
        import_profile.py          # 47.節のImportProfile

    exporters/
      word/
        base.py                    # Table/Row/Cell操作の共通ヘルパー（COM経由）
        fm05_v35.py
        fm05_v36.py
        registry.py                 # template_id+versionからExporterを解決
      excel/
        workbook_exporter.py
      pdf/
        pdf_exporter.py             # Word→ExportAsFixedFormatのラッパー

    templates/
      registry.json                 # 既知テンプレートのメタ情報（版数・ファイル名対応表）

    utils/
      uuid_utils.py
      validation.py
      unit_conversion.py

  tests/
    unit/
    integration/                    # Word COMが必要なテストはここに隔離
  logs/
  backup/
```

## 4. 各層の責務

### UI層
- 画面ごとにQt Widgetを持つが、**ロジックを持たない**。ユーザー操作をServiceのメソッド呼び出しに変換し、返ってきたDTO/モデルを表示するだけ。
- 構成図Editorのみ例外的に複雑なローカル状態（選択、ドラッグ中座標等）を持つが、確定操作（Undo対象になる操作）は必ず`DiagramService`経由でモデルを更新する。

### Service層
- 業務ルールの単一の置き場所。例：
  - `EquipmentService.set_parent(equipment_id, parent_id)` は循環参照チェック・自己参照禁止チェックをここで行う。
  - `EquipmentService.delete(equipment_id)` はCable参照数・子Equipment有無を調べ、呼び出し元（UI）に警告要否を返す（削除の可否判定とDB更新を分離し、確認ダイアログの表示はUI側の責務とする）。
- ImportServiceは各Importerの出力（`ImportCandidate`のリスト）を受け取り、確認画面向けのデータに整形するのみで、DB確定登録は「取り込む」ボタン押下時のみ行う。
- ExportServiceは「内部データ → DTO」への変換までを担当し、実際のWord/Excel/PDF生成はExporter層に委譲する。

### Repository層
- テーブル単位でCRUDメソッドのみを提供。JOINが必要な集約取得（例：Equipment+その子Equipment一覧）はRepositoryに用意してよいが、業務判断（削除してよいか等）は含めない。
- 全RepositoryはSQLite接続をDI（コンストラクタ引数）で受け取る。テストではin-memory SQLite（`:memory:`）に差し替え可能にする。

### Importer層
- 各Importer（Excel/Word/PDF/Image）は「ファイル→`ImportCandidate[]`」の変換のみを行う。`ImportCandidate`は共通の型（信頼度付き）で、Equipment候補・Cable候補等の種別を持つ。
- **Importerは絶対にDBへ書き込まない。** 確認画面を経由したユーザー確定操作のみがDB登録のトリガーになる（45.節・46.節）。
- OCR等の重い処理はここに閉じ込め、UIやServiceからは非同期実行結果（候補リスト）としてのみ見える。

### Exporter層
- 48.節の方針通り、Word Table/Row/Cellへの参照は**すべてこの層に閉じ込める**。GUIやServiceがセル位置を知ることは禁止。
- テンプレート版ごとにファイルを分離する（`fm05_v35.py` / `fm05_v36.py`）。`registry.py` が `TemplateDefinition.template_id + template_version` から適切なExporterクラスを解決する。未知のバージョンの場合は最も近い既知バージョンのExporterを暫定利用するのではなく、**明示的にエラーを出しユーザーに選択させる**（誤ったセルへの出力を防ぐため）。
- PDF/Excel出力は原則Word生成結果を再利用する（50.節・51.節）。独自PDFレンダリングエンジンは作らない。

## 5. 構成図とデータの関係

構成図（Diagram）は「Equipment/Cable/Connection/PowerSource/GroundConnectionという業務データ」と「DiagramNode/DiagramEdgeという表示座標データ」を分離する（26.節）。

- `diagram/scene.py` はDBの`DiagramNode`をQGraphicsItemに変換して表示するのみ。
- Qtの親子Item機能（`QGraphicsItem.setParentItem`）をそのまま`DiagramNode.parent_node_id`にマッピングする（29.節）。移動・リサイズ操作は`QUndoCommand`として実装し、確定時に`DiagramService`を通じて`DiagramNode`テーブルへ反映する。
- レンダリング（Word/PDF/Excel埋め込み用画像生成）はQGraphicsSceneを直接画面表示せずにオフスクリーンで`QSvgGenerator`等へ描画することで、画面表示用と出力用のロジックを共通化する（`renderer/svg_renderer.py`）。

## 6. 保存方式

- 1案件 = 1ファイル（`PJ260001.emcproj`）。実体はSQLiteデータベースファイルの拡張子を独自化したもの（6.節）。
- プロジェクトを開く＝そのファイルパスへSQLite接続を張る。「名前を付けて保存」は、接続を閉じてファイルをコピーしてから新しいパスへ再接続する。
- 自動保存：一定間隔（設定可能、既定300秒）でWALチェックポイント＋`backup/`への世代コピーを行う（61.節）。SQLiteのWALモードを使い、異常終了時のデータ損失を最小化する。
- 「最近使用したプロジェクト」はアプリ全体設定（`%APPDATA%/EmcReportTool/recent_projects.json`等）に保持し、プロジェクトファイル自体には含めない。

## 7. セキュリティ境界

- 標準ビルドでは、`importers/`・`exporters/`・OCR処理を含む全モジュールが外部ネットワーク呼び出しを行わないことをコードレビュー・依存パッケージ選定の両面で担保する（5.節）。
- 将来の外部AI拡張ポイントは `services/ai_extension/`（未実装、インターフェースのみ先行定義可）のような形で隔離し、既定では設定ファイルで無効化しておく。

## 8. エラーハンドリング方針

- Service層以下で発生した例外は、UI層の共通ハンドラでキャッチし、ユーザーには「処理中にエラーが発生しました。詳細はログを確認してください。」を表示、詳細は`logs/app.log`へ（60.節）。
- Word COM操作は失敗しやすい（Wordプロセスが残る、ファイルロック等）ため、`exporters/word/base.py`に共通の起動・後始末（`try/finally`でCOMオブジェクト解放、プロセスの確実な終了）を実装し、個別Exporterはビジネスロジックのみに専念する。

## 9. テスト戦略

- Repository・Service・Containment循環参照チェック・Import Mappingは純粋なUnit Testとしてモック不要（in-memory SQLite）で実行可能にする（65.節）。
- Word COMに依存するExporterのテストは`tests/integration/`に隔離し、CI環境でWordが無い場合はスキップ可能にする。
