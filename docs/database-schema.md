# データベーススキーマ設計（SQLite）

`docs/data-model.md` の論理モデルを実際のSQLite DDLへ落とし込む。1プロジェクト = 1 `.emcproj`（実体はSQLiteファイル）。

## 0. 共通方針

- 主キーはすべて `TEXT`（UUID文字列, 例: `36文字のUUID4`）。理由：インポート時・オフライン編集時に衝突しない永続IDが必要（13.節・19.節）。
- 外部キー制約を有効化する：接続時に必ず `PRAGMA foreign_keys = ON;` を実行する。
- `created_at` / `updated_at` は ISO8601文字列（UTC）で保持し、アプリ側でタイムゾーン変換する。
- 論理削除は採用しない（削除確認はService層のダイアログで担保し、DB上は物理削除する）。ただし`backup/`世代管理により誤削除からの復旧経路を別途確保する（61.節）。
- スキーマバージョンは `schema_migrations` テーブルで管理し、起動時に`database/migrations/*.sql`を順次適用する。

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);
```

## 1. Project / TemplateDefinition

```sql
CREATE TABLE projects (
    project_id              TEXT PRIMARY KEY,
    project_no              TEXT,
    test_plan_no             TEXT,
    measurement_period       TEXT,
    include_immunity         INTEGER NOT NULL DEFAULT 0,   -- boolean
    include_medical          INTEGER NOT NULL DEFAULT 0,
    include_taiwan           INTEGER NOT NULL DEFAULT 0,
    notes                     TEXT,
    created_at                TEXT NOT NULL,
    updated_at                TEXT NOT NULL
);

CREATE TABLE template_definitions (
    template_definition_id     TEXT PRIMARY KEY,
    project_id                  TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    template_id                 TEXT NOT NULL,     -- 例 "MM-QR-001/FM05"
    template_version             TEXT NOT NULL,     -- ファイル名由来 例 "3-6"
    template_internal_version    TEXT,              -- フッター等から読み取った値 例 "3-5"。不一致は許容しログのみ
    template_filename            TEXT NOT NULL,
    registered_at                 TEXT NOT NULL
);
```

## 2. Applicant / ReportStandard

```sql
CREATE TABLE applicants (
    applicant_id     TEXT PRIMARY KEY,
    project_id        TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    company_name_jp   TEXT,
    company_name_en   TEXT,
    address_jp        TEXT,
    address_en        TEXT,
    notes             TEXT
);

CREATE TABLE report_standards (
    report_standard_id  TEXT PRIMARY KEY,
    project_id            TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    standard_name          TEXT,
    language                TEXT CHECK(language IN ('jp','en')),
    desired_due_date        TEXT,
    submission_media        TEXT DEFAULT 'PDF',
    sort_order               INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_report_standards_project ON report_standards(project_id);
```

## 3. EutOverview / Frequency / OperationMode

```sql
CREATE TABLE eut_overviews (
    eut_overview_id         TEXT PRIMARY KEY,
    project_id                TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    kind_of_equipment          TEXT,
    model_name                  TEXT,
    serial_no                    TEXT,
    operating_program            TEXT,
    sample_type                   TEXT CHECK(sample_type IN ('mass_production','pre_production')),
    width_mm                      REAL,
    depth_mm                      REAL,
    height_mm                     REAL,
    max_frequency                  TEXT,
    wireless_frequency             TEXT,
    rating_power_supply_types      TEXT,   -- JSON配列文字列。例 '["dc_2p","single_phase_2p"]'
    rating_power_supply_value       TEXT,
    tested_condition                 TEXT,
    date_of_manufacture               TEXT,
    manufacturer_name                  TEXT,
    manufacturer_address                TEXT,
    attachment                           TEXT,
    option                                TEXT,
    date_sample_received                  TEXT,
    test_engineer                         TEXT
);

CREATE TABLE frequencies (
    frequency_id     TEXT PRIMARY KEY,
    eut_overview_id   TEXT NOT NULL REFERENCES eut_overviews(eut_overview_id) ON DELETE CASCADE,
    value              TEXT,
    unit                TEXT,
    usage_note           TEXT,
    sort_order            INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_frequencies_eut ON frequencies(eut_overview_id);

CREATE TABLE operation_modes (
    operation_mode_id  TEXT PRIMARY KEY,
    project_id           TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    mode_name              TEXT,
    description             TEXT,
    sort_order               INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_operation_modes_project ON operation_modes(project_id);
```

`rating_power_supply_types`をJSON配列文字列としたのは、Word側チェックボックスが複数選択可能（DC/1phase/3phaseそれぞれに2P/2P+E等のサブ選択がある）ため、正規化した子テーブルにするほどの検索要件が無い（このProject内でしか使わない）ことを踏まえた判断。将来集計要件が出た場合は`eut_power_supply_selections`子テーブルへ分離する。

## 4. Equipment（Containmentを含む）

```sql
CREATE TABLE equipments (
    equipment_id       TEXT PRIMARY KEY,
    project_id           TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    display_id             TEXT NOT NULL,      -- "A","B",... 表示専用、参照キーにしない
    category                TEXT NOT NULL CHECK(category IN ('EUT','Peripheral','AssociatedEquipment','Other')),
    description              TEXT,
    model_name                TEXT,
    serial                     TEXT,
    manufacturer                TEXT,
    fcc_id                       TEXT,
    bsmi_id                       TEXT,
    notes                          TEXT,
    placement_type                 TEXT NOT NULL DEFAULT 'standalone'
                                     CHECK(placement_type IN ('standalone','embedded','inserted','attached')),
    parent_equipment_id              TEXT REFERENCES equipments(equipment_id) ON DELETE SET NULL,
    sort_order                        INTEGER NOT NULL DEFAULT 0,
    created_at                          TEXT NOT NULL,
    updated_at                          TEXT NOT NULL,

    CHECK (equipment_id != parent_equipment_id)
);
CREATE INDEX idx_equipments_project ON equipments(project_id);
CREATE INDEX idx_equipments_parent ON equipments(parent_equipment_id);
```

**循環参照はDB制約だけでは検出できない**（多段階のためCHECK制約で表現不可）。したがって：
- `parent_equipment_id`更新は必ず`EquipmentService.set_parent()`を経由させ、アプリ側で祖先を辿るDFSチェックを行う。
- `ON DELETE SET NULL`を選択した理由：親Equipmentが（Serviceの確認ダイアログを経ずに万一）削除された場合でも、子Equipmentが道連れで消えることを避け、独立機器として残す安全側の挙動にするため。ただし通常の削除フローは57.節の確認ダイアログを必ず経由させる。

## 5. Cable（Connectionを兼ねる）

```sql
CREATE TABLE cables (
    cable_id            TEXT PRIMARY KEY,
    project_id            TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    cable_no                INTEGER NOT NULL,
    from_equipment_id         TEXT NOT NULL REFERENCES equipments(equipment_id) ON DELETE CASCADE,
    from_port                   TEXT,
    to_equipment_id               TEXT NOT NULL REFERENCES equipments(equipment_id) ON DELETE CASCADE,
    to_port                         TEXT,
    cable_type                       TEXT,
    length                             REAL,
    length_unit                         TEXT DEFAULT 'm',
    shielded                             TEXT CHECK(shielded IN ('shielded','non_shielded','unknown')) DEFAULT 'unknown',
    maximum_length                        TEXT,
    outdoor_connection                     TEXT CHECK(outdoor_connection IN ('yes','no','unknown')) DEFAULT 'unknown',
    notes                                    TEXT,
    sort_order                                INTEGER NOT NULL DEFAULT 0,
    created_at                                  TEXT NOT NULL,
    updated_at                                  TEXT NOT NULL
);
CREATE INDEX idx_cables_project ON cables(project_id);
CREATE INDEX idx_cables_from ON cables(from_equipment_id);
CREATE INDEX idx_cables_to ON cables(to_equipment_id);
```

`ON DELETE CASCADE`をfrom/toに設定：Equipment削除時に関連Cableも連動削除する（57.節の警告ダイアログで件数を提示した上でユーザーが削除を確定した場合の既定動作）。警告なしの誤操作を防ぐのはService層の責務であり、DB制約自体は「参照先が消えたら整合性を保つ」役割に徹する。

## 6. InlineComponent

```sql
CREATE TABLE inline_components (
    inline_component_id  TEXT PRIMARY KEY,
    cable_id                TEXT NOT NULL REFERENCES cables(cable_id) ON DELETE CASCADE,
    type                      TEXT NOT NULL CHECK(type IN
                                ('FerriteCore','ClampFilter','CommonModeFilter','Filter','Attenuator','Adapter','Other')),
    name                        TEXT,
    model                         TEXT,
    manufacturer                   TEXT,
    quantity                         INTEGER NOT NULL DEFAULT 1,
    position                           TEXT CHECK(position IN ('FromSide','Middle','ToSide')),
    notes                                TEXT,
    countermeasure_id                     TEXT REFERENCES countermeasures(countermeasure_id) ON DELETE SET NULL,
    sort_order                              INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_inline_components_cable ON inline_components(cable_id);
```

## 7. PowerSource / GroundConnection

```sql
CREATE TABLE power_sources (
    power_source_id  TEXT PRIMARY KEY,
    project_id         TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    kind                 TEXT NOT NULL CHECK(kind IN
                           ('AC100V','AC200V','DC24V','CommercialAC','StabilizedPowerSupply','ACPowerSupply','DCPowerSupply','Other')),
    label                  TEXT,
    notes                    TEXT
);

CREATE TABLE ground_connections (
    ground_connection_id  TEXT PRIMARY KEY,
    project_id              TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    kind                      TEXT NOT NULL CHECK(kind IN ('PE','FG','SignalGND','ChassisGND','Earth','Other')),
    label                       TEXT,
    notes                         TEXT
);
```

## 8. DiagramNode / DiagramEdge

```sql
CREATE TABLE diagram_nodes (
    node_id           TEXT PRIMARY KEY,
    project_id          TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    ref_type              TEXT NOT NULL CHECK(ref_type IN ('Equipment','PowerSource','GroundConnection')),
    ref_id                  TEXT NOT NULL,     -- 対応先のPK。ref_typeにより参照先テーブルが変わるためFK制約は付与しない（アプリ側で整合性確保）
    parent_node_id            TEXT REFERENCES diagram_nodes(node_id) ON DELETE SET NULL,
    x                           REAL NOT NULL DEFAULT 0,
    y                             REAL NOT NULL DEFAULT 0,
    relative_x                     REAL NOT NULL DEFAULT 0,
    relative_y                       REAL NOT NULL DEFAULT 0,
    width                              REAL NOT NULL DEFAULT 120,
    height                              REAL NOT NULL DEFAULT 80,
    z_order                              INTEGER NOT NULL DEFAULT 0,
    label_dx                              REAL NOT NULL DEFAULT 0,
    label_dy                                REAL NOT NULL DEFAULT 0,

    CHECK (node_id != parent_node_id)
);
CREATE INDEX idx_diagram_nodes_project ON diagram_nodes(project_id);
CREATE INDEX idx_diagram_nodes_parent ON diagram_nodes(parent_node_id);
CREATE UNIQUE INDEX idx_diagram_nodes_ref ON diagram_nodes(project_id, ref_type, ref_id);

CREATE TABLE diagram_edges (
    edge_id         TEXT PRIMARY KEY,
    project_id        TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    ref_type            TEXT NOT NULL CHECK(ref_type IN ('Cable')),
    ref_id                TEXT NOT NULL,      -- cables.cable_id（ref_type='Cable'の場合）
    route_points_json      TEXT,              -- JSON: [[x,y],[x,y],...]
    label_dx                 REAL NOT NULL DEFAULT 0,
    label_dy                   REAL NOT NULL DEFAULT 0
);
CREATE INDEX idx_diagram_edges_project ON diagram_edges(project_id);
CREATE UNIQUE INDEX idx_diagram_edges_ref ON diagram_edges(project_id, ref_type, ref_id);
```

`ref_id`にFK制約を付けない理由：`ref_type`によって参照先テーブルが`equipments`/`power_sources`/`ground_connections`と変わる多態的関連であり、SQLiteは条件付きFKを直接表現できないため。整合性は以下で担保する：
- Equipment/PowerSource/GroundConnectionを削除するService処理内で、対応する`diagram_nodes`行も同一トランザクションで削除する。
- Cableを削除するService処理内で、対応する`diagram_edges`行も同一トランザクションで削除する。
- 起動時整合性チェック（任意）：`diagram_nodes.ref_id`が対応テーブルに存在するかを検証するユーティリティを`tools/`に用意し、破損データを検出できるようにする。

## 9. Countermeasure

```sql
CREATE TABLE countermeasures (
    countermeasure_id     TEXT PRIMARY KEY,
    project_id               TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    description                TEXT,
    component_model              TEXT,
    component_manufacturer         TEXT,
    sort_order                       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_countermeasures_project ON countermeasures(project_id);
```

（`inline_components.countermeasure_id`が本テーブルを参照するため、マイグレーションファイルでは`countermeasures`を`inline_components`より先に作成すること。）

## 10. ImmunityCriteria

```sql
CREATE TABLE immunity_criteria (
    immunity_criteria_id  TEXT PRIMARY KEY,
    project_id               TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    criterion_a                 TEXT,
    criterion_b                   TEXT,
    criterion_c                     TEXT
);

CREATE TABLE immunity_verification_points (
    point_id                  TEXT PRIMARY KEY,
    immunity_criteria_id        TEXT NOT NULL REFERENCES immunity_criteria(immunity_criteria_id) ON DELETE CASCADE,
    content                        TEXT,
    sort_order                       INTEGER NOT NULL DEFAULT 0
);
```

## 11. MedicalCriteria

```sql
CREATE TABLE medical_criteria (
    medical_criteria_id     TEXT PRIMARY KEY,
    project_id                 TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    immunity_performance_text     TEXT
);

CREATE TABLE medical_criteria_items (
    item_id                 TEXT PRIMARY KEY,
    medical_criteria_id        TEXT NOT NULL REFERENCES medical_criteria(medical_criteria_id) ON DELETE CASCADE,
    category                      TEXT NOT NULL CHECK(category IN ('basic_safety','basic_performance')),
    content                         TEXT,
    sort_order                       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_medical_items_criteria ON medical_criteria_items(medical_criteria_id);
```

## 12. TaiwanApplicant / TaiwanFactory / InternalComponent

```sql
CREATE TABLE taiwan_applicants (
    taiwan_applicant_id      TEXT PRIMARY KEY,
    project_id                  TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    company_name_en                TEXT,
    address_en                       TEXT,
    company_name_zh                    TEXT,
    address_zh                           TEXT,
    notes                                   TEXT,
    eut_operation_status_text                 TEXT
);

CREATE TABLE taiwan_factories (
    taiwan_factory_id       TEXT PRIMARY KEY,
    taiwan_applicant_id        TEXT NOT NULL REFERENCES taiwan_applicants(taiwan_applicant_id) ON DELETE CASCADE,
    company_name                  TEXT,
    address                          TEXT,
    sort_order                         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE internal_components (
    internal_component_id    TEXT PRIMARY KEY,
    taiwan_applicant_id         TEXT NOT NULL REFERENCES taiwan_applicants(taiwan_applicant_id) ON DELETE CASCADE,
    device_name                    TEXT,
    quantity_max                     TEXT,
    model_name                         TEXT,
    manufacturer                         TEXT,
    sort_order                             INTEGER NOT NULL DEFAULT 0
);
```

## 13. Import関連

```sql
CREATE TABLE import_sources (
    import_source_id    TEXT PRIMARY KEY,
    project_id             TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    source_type              TEXT NOT NULL CHECK(source_type IN ('excel','word','pdf','image')),
    file_path                  TEXT,
    imported_at                  TEXT NOT NULL,
    status                         TEXT NOT NULL DEFAULT 'pending_review'
                                     CHECK(status IN ('pending_review','applied','discarded'))
);

CREATE TABLE import_candidates (
    candidate_id         TEXT PRIMARY KEY,
    import_source_id        TEXT NOT NULL REFERENCES import_sources(import_source_id) ON DELETE CASCADE,
    target_entity_type         TEXT NOT NULL CHECK(target_entity_type IN ('equipment','cable')),
    payload_json                  TEXT NOT NULL,
    confidence                      TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
    status                            TEXT NOT NULL DEFAULT 'pending'
                                        CHECK(status IN ('pending','accepted','rejected'))
);
CREATE INDEX idx_import_candidates_source ON import_candidates(import_source_id);
```

`ImportProfile`（顧客別マッピング）はプロジェクトを跨いで再利用する性質が強いため、**プロジェクトDBには含めず、アプリ全体設定として別ファイル**（例：`%APPDATA%/EmcReportTool/import_profiles.sqlite`、またはJSON）で管理する。理由：プロジェクトファイル（`.emcproj`）を配布・アーカイブする際に、他社の顧客マッピング情報が意図せず同梱されるのを避けるため。

```sql
-- import_profiles.sqlite (アプリ全体設定DB、プロジェクトDBとは別ファイル)
CREATE TABLE import_profiles (
    import_profile_id   TEXT PRIMARY KEY,
    customer_name           TEXT NOT NULL,
    field_mapping_json         TEXT NOT NULL,   -- {"Device Name":"description", ...}
    created_at                   TEXT NOT NULL,
    updated_at                     TEXT NOT NULL
);
```

## 14. マイグレーション適用順序

外部キー依存関係により、以下の順序で `0001_initial.sql` を構成する：

1. `schema_migrations`
2. `projects`
3. `template_definitions`, `applicants`, `report_standards`
4. `eut_overviews` → `frequencies`
5. `operation_modes`
6. `equipments`（自己参照）
7. `countermeasures`
8. `cables`（equipmentsに依存）
9. `inline_components`（cables, countermeasuresに依存）
10. `power_sources`, `ground_connections`
11. `diagram_nodes`（自己参照）, `diagram_edges`
12. `immunity_criteria` → `immunity_verification_points`
13. `medical_criteria` → `medical_criteria_items`
14. `taiwan_applicants` → `taiwan_factories`, `internal_components`
15. `import_sources` → `import_candidates`

## 15. 既存プロジェクトファイルとの互換性（development-plan.md 76.節対応）

- スキーマ変更は必ず新しい`NNNN_xxx.sql`を追加する形で行い、既存マイグレーションファイルは変更しない。
- 破壊的変更（カラム削除・型変更）が必要な場合でも、旧カラムのデータを新カラムへ移行するマイグレーションを必ず用意し、単純な`DROP COLUMN`のみで済ませない。
- アプリ起動時、開いた`.emcproj`の`schema_migrations`最大バージョンを見て、未適用のマイグレーションのみ順次適用する。適用前に`backup/`へ自動バックアップを取得してから実行する。
