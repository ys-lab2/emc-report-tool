# データモデル設計

## 1. 最重要原則：4概念の分離

指示書77.節の通り、以下の4つは**別々のデータ**として扱い、決して混同しない。

| 概念 | 意味 | 例 |
|---|---|---|
| **Containment（内包）** | 機器が物理的に別の機器の中に存在する／取り付けられている | SDカードがPCの中にある |
| **Connection（接続）** | 機器同士がケーブルで電気的に接続されている | PCとEUTがUSB接続されている |
| **Cable（ケーブル実体）** | 接続に使われる物理的な線そのもの | USB Cable 2m Shielded |
| **InlineComponent（線上部品）** | ケーブル上に取り付けられた部品 | フェライトコア |

Containmentが存在すること（BがA内部にある）は、ConnectionでAとBが結ばれることを一切意味しない。両者は完全に独立したテーブル・独立した参照系として設計する（16.節・20.節）。

## 2. エンティティ関連図（概念レベル）

```
Project 1───1 Applicant
Project 1───1 EutOverview
Project 1───* ReportStandard
Project 1───* Frequency            (EutOverviewにぶら下がる周波数一覧)
Project 1───* OperationMode
Project 1───* Equipment
Project 1───* Cable
Project 1───* Connection
Project 1───* PowerSource
Project 1───* GroundConnection
Project 1───* Countermeasure
Project 1───1 ImmunityCriteria
Project 1───1 MedicalCriteria
Project 1───1 TaiwanApplicant
Project 1───* InternalComponent    (TaiwanApplicantにぶら下がる)
Project 1───1 DiagramCanvas設定    (zoom等)
Project 1───* ImportSource
Project 1───* ImportProfile (アプリ全体設定として共有される場合もある)
Project 1───1 TemplateDefinition

Equipment 1───* Cable  (from_equipment_id)
Equipment 1───* Cable  (to_equipment_id)
Equipment 1───* Equipment (parent_equipment_id によるContainment、自己参照)
Equipment 1───1 DiagramNode

Cable 1───* InlineComponent
Cable 1───1 Connection相当（Connectionは概念上Cableのfrom/toと同じ情報を持つため、実装上はCable自体がConnection情報を内包する。詳細は3.節参照）

DiagramNode 1───* DiagramNode (parent_node_id、自己参照、Equipmentの親子と対応)
DiagramNode 1───* DiagramEdge (Cable/PowerSource/GroundConnectionの描画情報)
```

## 3. Connection と Cable の関係について（設計判断）

指示書19.節では「Connectionは From Equipment → Cable → To Equipment」という表現をしているが、21.節のCable項目には既に `from_equipment_id` / `to_equipment_id` に相当する情報（From/To Port含む）が含まれる。

これを踏まえ、本設計では **Connectionを独立テーブルにはせず、Cableエンティティ自体がConnection情報（from/to）を持つ**方式を採用する。理由：

- 1本のCableは必ず1つのFrom/Toを持つ（同一Cableが複数のConnectionを持つケースは実運用上存在しない）。
- Connectionを別テーブルにすると「CableとConnectionの1:1関係を常に維持する」という余計な整合性制約が増えるだけで、指示書が警戒する「Containment(親子関係)とConnection(接続)の混同」の防止には寄与しない。
- 指示書16.節の本質的要求は「親子関係テーブル（Equipment.parent_equipment_id）」と「接続関係テーブル（Cable）」を混同しないことであり、これは別テーブルとして満たされる。

ただし将来「1本の物理ケーブルが分岐して3台に接続される」等の要件が出た場合に備え、`Cable`と`from/to`の間に`CableEndpoint`を挟む拡張余地はコメントとして残すが、**現時点では実装しない**（52.節のEntity一覧に`Connection`が明示されているため、DBスキーマ上は`cables`テーブルが実質的に`Connection`を兼ねることをコメントで明記し、将来分離が必要になった場合の移行パスを`database-schema.md`に記載する）。

## 4. Equipment（機器）

```
Equipment
  equipment_id       : UUID (PK, 内部参照キー)
  project_id         : UUID (FK)
  display_id         : str          # "A", "B", "C"... ユーザー表示用。DB参照キーにしない (19.節)
  category           : enum         # EUT / Peripheral / AssociatedEquipment / Other
  description        : str
  model_name         : str
  serial             : str
  manufacturer       : str
  fcc_id             : str | null
  bsmi_id            : str | null
  notes              : str
  placement_type     : enum         # standalone / embedded / inserted / attached
  parent_equipment_id: UUID | null (FK -> Equipment.equipment_id)
  sort_order         : int          # display_id自動採番・表示順の補助
  created_at / updated_at
```

**Containmentのルール（14.節・15.節）：**
- `parent_equipment_id = NULL` の場合は独立機器（standalone扱いだが、`attached`＝外付け取付でも親を持たないケースがあるため、`placement_type`と`parent_equipment_id`は独立した項目として保持する。`placement_type = embedded/inserted`のときのみ`parent_equipment_id`必須というバリデーションをService層で行う）。
- 自己参照禁止：`equipment_id == parent_equipment_id`はService層で拒否。
- 循環参照禁止：`EquipmentService.set_parent()`実行時に、祖先を辿って自分自身が現れないかチェックする（DFS、深さは実務上数段で十分だが再帰関数として深さ無制限に対応する）。
- 多段階内包（A→B→C）をDBレベルで許可する。GUIの初期実装が1〜2階層に制限されていても、テーブル定義・Repository・循環参照チェックロジックは常に再帰対応で実装する（15.節）。

## 5. Cable（ケーブル、Connectionを兼ねる）

```
Cable
  cable_id           : UUID (PK)
  project_id         : UUID (FK)
  cable_no           : int              # Word出力上のNo.、表示用
  from_equipment_id  : UUID (FK -> Equipment)
  from_port          : str
  to_equipment_id    : UUID (FK -> Equipment)
  to_port            : str
  cable_type         : str
  length             : float | null
  length_unit        : enum             # m / cm / ft 等
  shielded           : enum             # shielded / non_shielded / unknown
  maximum_length     : str              # 製造者仕様上限（自由記述、"〇〇m以下"のような表記を許容）
  outdoor_connection : enum             # yes / no / unknown
  notes              : str
  sort_order         : int
  created_at / updated_at
```

- `from_equipment_id` / `to_equipment_id` は必ずEquipmentの内部UUIDを参照する。表示用の `display_id`（A, B, C...）はDB参照キーとして絶対に使わない（19.節）。
- 内包されているEquipment（子Equipment）も通常のEquipmentと全く同じ扱いでCableの `from/to` に指定可能（20.節）。Containmentの有無はConnectionの可否と無関係。
- 同一Equipmentペア間に複数Cableを許可する（18.節）。一意制約は `cable_id` のみで、`(from,to)`の組み合わせに対する一意制約は設けない。

## 6. InlineComponent（ケーブル線上部品）

```
InlineComponent
  inline_component_id : UUID (PK)
  cable_id             : UUID (FK -> Cable)
  type                 : enum          # FerriteCore / ClampFilter / CommonModeFilter / Filter / Attenuator / Adapter / Other
  name                 : str
  model                : str
  manufacturer         : str
  quantity             : int
  position             : enum          # FromSide / Middle / ToSide
  notes                : str
  sort_order           : int
```

フェライト専用モデルにせず汎用化する（21.節）。1本のCableに複数登録可能。将来`Countermeasure`（EMC対策）とのリンクのため、`countermeasure_id : UUID | null`（FK, nullable）を任意項目として持たせておく（34.節「可能であれば構成図上のInlineComponentとリンク可能にする」への対応）。

## 7. PowerSource（電源）・GroundConnection（GND）

```
PowerSource
  power_source_id : UUID (PK)
  project_id       : UUID (FK)
  kind             : enum       # AC100V / AC200V / DC24V / CommercialAC / StabilizedPowerSupply / ACPowerSupply / DCPowerSupply / Other
  label            : str        # 自由記述の補足表示
  notes            : str

GroundConnection
  ground_connection_id : UUID (PK)
  project_id             : UUID (FK)
  kind                   : enum   # PE / FG / SignalGND / ChassisGND / Earth / Other
  label                  : str
  notes                  : str
```

PowerSource/GroundConnectionはEquipmentとは別のNodeとして構成図上に配置される（22.節・23.節）。これらから機器への接続線（構成図上のエッジ）は`DiagramEdge`で表現し、業務データとしての「電源ケーブルの型式」等の詳細管理が必要になった場合は`Cable`同様の拡張を検討するが、現行Word帳票に電源ケーブル明細の欄が無いため、初期実装では`DiagramEdge`（見た目の線のみ）で十分とする。

## 8. DiagramNode / DiagramEdge（構成図の表示データ）

```
DiagramNode
  node_id       : UUID (PK)
  project_id    : UUID (FK)
  ref_type      : enum          # Equipment / PowerSource / GroundConnection
  ref_id        : UUID          # 対応するEquipment/PowerSource/GroundConnectionのID
  parent_node_id: UUID | null (FK -> DiagramNode, 自己参照)
  x, y          : float         # 絶対座標（parent_node_id = NULLのノードで意味を持つ）
  relative_x, relative_y : float  # 親ノード基準の相対座標（parent_node_id != NULLのノードで使用）
  width, height : float
  z_order       : int
  label_dx, label_dy : float    # ラベル位置の親要素からのオフセット (30.節・33.節)

DiagramEdge
  edge_id       : UUID (PK)
  project_id    : UUID (FK)
  ref_type      : enum          # Cable / (将来的にPowerLine等)
  ref_id        : UUID          # 対応するCable.cable_id
  route_points  : JSON          # [(x,y), (x,y), ...] 折れ線の中間点列 (30.節)
  label_dx, label_dy : float
```

- `DiagramNode`はEquipmentそのものと1:1対応するが、あえて別テーブルにすることで「業務データ（Equipment）」と「表示データ（座標・サイズ）」を分離する（26.節）。
- 子Equipmentに対応する`DiagramNode`は`parent_node_id`が親EquipmentのNode IDを指し、通常は`relative_x/relative_y`で親基準の位置を保持する。親を移動した場合、子の`relative_*`は変更不要（親のx,yだけ更新すればよい）（26.節・25.節）。
- `DiagramEdge`は`Cable`の`from/to`情報を再利用し、線の見た目（ルート・ラベル位置）だけをここで管理する。Cable自体を削除すれば対応する`DiagramEdge`も削除する（カスケード）。

## 9. Project 直下の単純エンティティ群

```
Applicant
  applicant_id, project_id
  company_name_jp, company_name_en
  address_jp, address_en
  notes

ReportStandard
  report_standard_id, project_id
  standard_name
  language              # jp / en
  desired_due_date
  submission_media      # PDF / Paper / etc

EutOverview  (Project 1:1)
  eut_overview_id, project_id
  kind_of_equipment, model_name, serial_no
  operating_program
  sample_type                 # mass_production / pre_production
  width, depth, height
  max_frequency
  wireless_frequency
  rating_power_supply_type    # DC_2P / DC_2P_E / SinglePhase_2P / ... (複数選択のためJSON配列 or 別テーブルFrequencySelectionでも可。詳細はdatabase-schema.md)
  rating_power_supply_value   # 電圧・電流の自由記述
  tested_condition
  date_of_manufacture
  manufacturer_name, manufacturer_address
  attachment, option
  date_sample_received
  test_engineer

Frequency  (EutOverviewに対する周波数一覧、複数行)
  frequency_id, eut_overview_id
  value, unit, usage_note

OperationMode
  operation_mode_id, project_id
  mode_name
  description
  sort_order

Countermeasure
  countermeasure_id, project_id
  description
  component_model, component_manufacturer
  sort_order

ImmunityCriteria (Project 1:1)
  immunity_criteria_id, project_id
  criterion_a, criterion_b, criterion_c
  verification_points   : JSON配列 or 別テーブル ImmunityVerificationPoint

MedicalCriteria (Project 1:1)
  medical_criteria_id, project_id
  basic_safety_items      : 別テーブル MedicalCriteriaItem (category='basic_safety')
  basic_performance_items : 別テーブル MedicalCriteriaItem (category='basic_performance')
  immunity_performance_text

TaiwanApplicant (Project 1:1)
  taiwan_applicant_id, project_id
  company_name_en, address_en
  company_name_zh, address_zh
  factory_name, factory_address     # 複数工場に備え別テーブル化も検討 (下記参照)
  notes
  eut_operation_status_text

InternalComponent  (TaiwanApplicantに対する内部構成品リスト)
  internal_component_id, taiwan_applicant_id
  device_name, quantity_max, model_name, manufacturer
  sort_order
```

Table 13の実測（`docs/word-template-analysis.md` 3.節）では「工場名」に会社名・住所のペアが2セット存在したため、`factory_name/factory_address`を単純な2カラムにせず、`TaiwanFactory`という子テーブル（`taiwan_applicant_id`に対して複数行）として持たせることを推奨する（詳細は`database-schema.md`）。

## 10. AdditionalDocumentSelection（追加資料選択）

```
Project.include_immunity : bool
Project.include_medical  : bool
Project.include_taiwan   : bool
```

38.節の「☑Immunity ☑Medical ☑Taiwan」はProjectの3つのbooleanフラグとして持つ。ImmunityCriteria/MedicalCriteria/TaiwanApplicantのレコード自体は常に作成してよい（未選択でも空データとして保持し、消さない）。フラグはWord出力時にどのページ（追加資料A/B/D）を出力するかの制御にのみ使う。

## 11. ImportSource / ImportProfile / TemplateDefinition

```
ImportSource
  import_source_id, project_id
  source_type          # excel / word / pdf / image
  file_path
  imported_at
  status                # pending_review / applied / discarded

ImportCandidate  (ImportSourceに対する候補、DB保存は任意。UIセッション内メモリのみでも良いが、後から見返せるよう保存する)
  candidate_id, import_source_id
  target_entity_type    # equipment / cable / connection
  payload               : JSON
  confidence            # high / medium / low
  status                 # pending / accepted / rejected

ImportProfile
  import_profile_id
  customer_name
  field_mapping          : JSON   # {"Device Name": "description", "P/N": "model_name", ...}
  # プロジェクトを跨いで再利用されるため、プロジェクト単位ではなくアプリ全体設定として別DB/設定ファイルに保持することも検討可（database-schema.mdで方針確定）

TemplateDefinition (Project 1:1)
  template_id            # 例 "MM-QR-001/FM05"
  template_version        # ファイル名由来のバージョン、例 "3-6"
  template_internal_version # フッター等、文書内部から読み取ったバージョン文字列。存在すれば保持
  template_filename
  registered_at
```

`template_version`と`template_internal_version`が不一致の場合、Import/Export時にログへ警告を出すのみで処理は止めない（word-template-analysis.md 0.節の実例に対応）。

## 12. データ整合性ルールまとめ（57.節・58.節）

| 操作 | ルール |
|---|---|
| Equipment削除 | 参照しているCableが存在する場合、件数を提示して警告（続行するとCable側のfrom/toが不整合になるため、実装上はCable側も連動削除するか、from/toをNULL化するかを選択させる。本設計ではCascade Delete＝関連Cableも削除、を既定動作としつつ確認ダイアログで明示する） |
| 親Equipment削除（子あり） | 「子機器も削除する」「子機器を独立機器に変更する（parent_equipment_id=NULLにする）」「キャンセル」の3択 |
| Equipment.parent_equipment_id設定 | 自己参照禁止、循環参照禁止（DFSチェック） |
| Cable.from/to | 存在しないEquipmentへの参照を禁止（FK制約 + Service層バリデーション） |
| Cable.length | 数値以外を許容しない（ただし空欄は許容） |
| 必須項目 | Model等は未入力でも保存可能。測定途中の未確定状態での保存を常に許容する（過剰なNOT NULL制約を設けない） |
| display_id | 重複時は警告のみ（一意制約はDBレベルでは設けない、UI側で警告表示） |

## 13. 将来のConnection分離への移行パス（参考）

もし将来「1本のケーブルが複数機器に分岐する」等の要件が生じた場合：
1. 新テーブル `connections(connection_id, cable_id, equipment_id, port, role[from/to])` を追加。
2. 既存`cables.from_equipment_id/to_equipment_id`はマイグレーションで`connections`に変換し、カラム自体は後方互換のため一定期間残す（またはビューとして再現）。
3. Exporter/Service層は`Cable.get_connections()`のようなアクセサ越しにfrom/toを取得するよう先に抽象化しておくと、この移行が局所化される。

現時点ではこの抽象化レイヤーの先行実装は行わない（過剰設計を避ける、44.節「YAGNI」的な指示書の全体方針に合わせる）が、Repository層のインターフェース名は`get_from_equipment()`/`get_to_equipment()`のような形にしておき、内部実装がカラム直参照でも将来差し替えやすくしておく。
