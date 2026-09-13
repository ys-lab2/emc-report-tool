# Word テンプレート解析（MM-QR-001/FM05）

対象ファイル：
`テンプレート/MM-QR-001_FM05_テストレポート作成資料_Ver.3-6 (2025.03.25).docx`

本ドキュメントは `python-docx` および OOXML 直接解析により、上記ファイルを実際に開いて調べた結果である。伝聞や過去の記憶ではなく、このファイルそのものから抽出した事実のみを記載する。

## 0. 最重要な発見：バージョン表記の不一致

**ファイル名のバージョンと、文書内部（フッター）に印字されているバージョンが一致していない。**

| 場所 | 値 |
|---|---|
| ファイル名 | `Ver.3-6 (2025.03.25)` |
| フッター文字列（実テキスト） | `Form No.MM-QR-001/FM05 Ver.3-5 (2024.08.02)` |
| Word コアプロパティ `revision` | `20` |
| 最終更新者 | KURODA Ryuki |
| 最終更新日 | 2025-04-25 |

つまり、ファイルは `Ver.3-6` として配布されているが、Word 文書内部のフッターは古い `Ver.3-5` のまま更新されていない（差し替え漏れ、または意図的に版数を上げずに軽微修正した可能性がある）。

この事実は、指示書 2. で述べられている懸念（「添付ファイル名のバージョンとWord内部に記載されているForm Versionが一致していない可能性がある」）が **実際に発生している** ことを裏付ける。

**設計への反映：**
- `template_version` は「ファイル名から取る」「フッター文字列から取る」のどちらか一方に決め打ちしない。
- `TemplateDefinition` エンティティは、ファイル名由来のバージョンとフッター由来のバージョン文字列を **両方** 保持できるようにし、一致しない場合は警告をログに出すのみで処理は継続する（詳細は `docs/data-model.md` の `TemplateDefinition` を参照）。
- コード内に `"3-6"` のような版数文字列をハードコードしない。バージョン判定はテンプレート登録時にユーザーが確認・確定する運用とする。

## 1. 文書全体構造

- セクション数：1（`w:sectPr` は文末に1つのみ）
- 明示的な改ページ（`w:br type="page"`）：8箇所 → 論理的に9ページ構成
- 表（`w:tbl`）：14個（すべて本文直下の単純な表。ネストした表は無し）
- コンテンツコントロール（`w:sdt`）：11個、すべて **チェックボックス型**。タグ／エイリアスは未設定（`w:tag` / `w:alias` なし）
- ブックマーク（`w:bookmarkStart`）：**0個**（既存テンプレートにはブックマークが一切無い）
- 画像：本文中に1個（PNG、システム構成図の記入例）＋ ヘッダー内に2個（1個はアンカー配置＝ロゴ等の可能性、1個はインライン）
- ヘッダーに `PAGE` / `NUMPAGES` フィールドあり（キャッシュ表示値は "7 of 7"。本文の実ページ数（9）と食い違うが、これは最後に自動計算された時点のキャッシュ値であり、Word側で開けば再計算される。実装上は無視してよい）

## 2. ページ構成（改ページ位置から実測）

| Page | 内容 | 対応 Table Index |
|---|---|---|
| 1 | プロジェクト情報（プロジェクト番号／テストプラン番号／測定期間）、レポート作成規格一覧、申請者情報 | Table 0, 1, 2 |
| 2 | 装置概要（A〜Q全項目、1枚の大きな表） | Table 3 |
| 3 | 供試装置及び使用した周辺装置（EUT / Peripherals / Associated Equipment） | Table 4 |
| 4 | 使用したケーブル一覧 | Table 5 |
| 5 | 試験時配置図・システム構成図（記入例つき）、EMC対策内容 | Table 6, 7, 8 |
| 6 | 追加資料A：イミュニティ試験時の追加資料（性能基準A/B/C、動作確認箇所） | Table 9 |
| 7 | 追加資料B：医療規格用の追加資料（基礎安全／基本性能／イミュニティ試験時の性能基準の判定基準） | Table 10 |
| 8 | 追加資料C：医療規格用／性能基準に関する参考資料（IEC 60601-4-2、固定文言の参考情報） | Table 11, 12 |
| 9 | 追加資料D：台湾測定用の追加資料（申請者情報、EUT内部構成品リスト、試験時のEUT動作状態） | Table 13 |

指示書の「1ページ目〜7ページ目以降」という説明は概ね合っているが、実測では**装置概要だけで1ページ全部（Table 3が24行）**を使い、機器リストとケーブルリストはそれぞれ独立したページになっている。実装（特に自動改ページやページ数見積り）はこの実測値を基準にする。

## 3. 表ごとの詳細マッピング

### Table 0（Page 1）— プロジェクト基本情報
3行2列。ラベルセルと入力セルの単純な縦積み。

| 行 | ラベル | アプリ側フィールド |
|---|---|---|
| R0 | プロジェクト番号 | `Project.project_no` |
| R1 | テストプラン番号 | `Project.test_plan_no` |
| R2 | 測定期間 | `Project.measurement_period` |

### Table 2（Page 1）— レポート作成規格 + 申請者情報
15行8列。列0-2は縦結合された見出しセル（「レポート作成規格」「Applicant / 申請者」）。実質的な入力列は列3〜7。

- R1: ヘッダー行（No. / 規格名 / 和文・英文 / 希望納期 / 提出媒体）
- R2〜R9: 規格明細行（最大8規格）。列7の初期値は "PDF"（提出媒体のデフォルト）
- R10〜R13: 申請者情報（会社名・住所を和文/英文で記入する構造。セル結合が多く、python-docx の `cell.text` では重複表示されるため、Word出力時は実際のセル結合構造（`w:gridSpan` / `w:vMerge`）をそのまま使い、アプリ側では「規格の行数」「申請者情報のブロック」という論理単位で管理する）

`ReportStandard`（規格）は台数上限を8とせず、アプリ内部では可変長リストとして持ち、Word出力時に既存8行に収まらない場合は行を複製する（9.のテンプレート変更方針を参照）。

### Table 3（Page 2）— 装置概要
24行5列。列0が表示ラベル（A〜Q）、列1-2が項目名（日英併記）、列3-4が入力欄（結合セル、注記行が交互に入る）。

| 表示ID | 項目 | アプリフィールド |
|---|---|---|
| A | Kind of Equipment | `EutOverview.kind_of_equipment` |
| B | Model name | `EutOverview.model_name` |
| C | Serial No | `EutOverview.serial_no` |
| D | Operating program used | `EutOverview.operating_program` |
| E | Type of Sample Tested | `EutOverview.sample_type`（チェックボックス：Mass-production / Pre-production） |
| F | Dimension(mm) | `EutOverview.width` / `depth` / `height` |
| G | High Frequency Used | `EutOverview.max_frequency` + `Frequency[]`（一覧） |
| H | Wireless frequency | `EutOverview.wireless_frequency` |
| I | Rating Power Supply | `EutOverview.rating_power_supply_type`（チェックボックス：DC 2P/2P+E、1phase 2P/2P+E、3phase 3P(Δ)+E/4P(Y)+E）+ 数値（電圧/電流） |
| J | Tested Condition | `EutOverview.tested_condition` |
| K | Date of Manufacture | `EutOverview.date_of_manufacture` |
| L | Manufacturer | `EutOverview.manufacturer_name` / `manufacturer_address` |
| M | Attachment | `EutOverview.attachment` |
| N | Option | `EutOverview.option` |
| O | Operation mode | `OperationMode[]`（モード名 + 説明の繰り返し） |
| P | Date of Sample Received | `EutOverview.date_sample_received` |
| Q | Test Engineer | `EutOverview.test_engineer` |

**チェックボックス（コンテンツコントロール）実測：**
- E) Type of Sample Tested: `☐ Mass-production` / `☐ Pre-production`（2個）
- I) Rating Power Supply: `☐DC(☐2P/☐2P+E)` `☐1phase(☐2P/☐2P+E)` `☐3phase(☐3P(Δ)+E/☐4P(Y)+E)`（9個）

これらは `w:sdt` の `checkbox` 型で、タグ名が設定されていないため、Word出力時は **セル内のチェックボックス出現順** に依存してインデックスでチェック状態を設定する必要がある（テンプレート変更に弱い箇所。8.節で後述する対応方針を参照）。

### Table 4（Page 3）— 機器リスト
19行6列。カテゴリごとに見出し行があり、その下に表示ID（A〜N）の行が続く。

- R2: 見出し「供試装置 / EUT」→ R3-R5: A, B, C
- R6: 見出し「周辺機器 / Peripherals」→ R7-R12: D, E, F, G, H, I
- R13: 見出し「対向機 / Associated Equipment」→ R14-R18: J, K, L, M, N

列構成：No. / Description / Model / Serial / Manufacturer / FCC ID・BSMI ID（列5、脚注※1※2参照）

この構造から、**現行帳票は A〜N の14行（EUT最大3、Peripheral最大6、Associated最大5）が固定行数の表**であることが分かる。指示書13.の通り、アプリ内部では台数上限を固定しないが、Word出力時は「テンプレートの行数に収まる限りは既存行を使う、超える場合は行を複製する」処理が必須になる（複製時はセル罫線・フォントを直前行からコピーする）。

### Table 5（Page 4）— 使用したケーブル一覧
17行6列。R3〜R16 が明細行（最大14本）。列：No. / Cable Type / Length(m) / Shielded(Non-shielded/Shielded) / 製造者仕様接続上限長さ / 屋外へ直接接続(する・しない)。

R3 に記入例（"1 | | | Non-shielded/Shielded | 〇〇ｍ以下 | する・しない"）が残っている＝これはプレースホルダのテキストであり、実際の出力時はこの例文を上書きする。

### Table 6, 7（Page 5）— 構成図
Table 6（1行1列）は見出しのみ。Table 7（1行1列）に PNG 画像（記入例の構成図）が1枚埋め込まれている。実際の構成図はこの1×1セル内に画像として挿入する運用になっている＝**アプリの構成図エディタで生成したレンダリング画像（SVG→PNG/EMF）を、このセルの中身として差し替える**のがWord出力の基本方針（49.節の方針と一致）。

### Table 8（Page 5）— EMC対策内容
2行1列。R0が見出し、R1が注記＋自由記述欄。`Countermeasure[]` を箇条書きテキストとして流し込む。

### Table 9（Page 6）— イミュニティ性能基準（追加資料A）
4行2列。Performance criterion A/B/C の3行 + 見出し行。`ImmunityCriteria.criterion_a/b/c`にマッピング。直後に「動作確認箇所」の箇条書き段落（Table外、3行の "・" プレースホルダ）があり、これは `ImmunityCriteria.verification_points`（可変長リスト）として保持し、Word出力時に段落を複製する。

### Table 10（Page 7）— 医療規格 判定基準（追加資料B）
14行2列。B.1基礎安全（5行）、B.2基本性能（5行）、B.3イミュニティ試験時の性能基準（自由記述）。`MedicalCriteria.basic_safety[]` / `basic_performance[]` / `immunity_performance_text` にマッピング。

### Table 11, 12（Page 8）— 医療規格参考資料（追加資料C）
これは**編集不要の固定参考テキスト**（IEC 60601-4-2の一般的な説明文）。アプリ側でデータとして管理する必要は無く、テンプレートにそのまま残す静的ページとして扱う。

### Table 13（Page 9）— 台湾資料（追加資料D）
29行6列。
- R1-R8: 申請者情報（英語/繁体字の会社名・住所）、工場名（会社名・住所×2セット）
- R9: 備考欄
- R11-R26: C.2 EUTの内部構成品リスト（装置名／数量(Max)／モデル名／製造者、最大16行）
- R27-R28: C.3 試験時のEUTの動作状態（自由記述）

`TaiwanApplicant` + `InternalComponent[]` にマッピング。

## 4. ヘッダー／フッター

- ヘッダー1行目：`このシートにはなるべく測定当日に測定担当者が記入して下さい。`（固定文言、全ページ共通）
- ヘッダー2行目：`Page {PAGE} of {NUMPAGES}` フィールド ＋ `テストレポート作成資料`（固定タイトル）
- フッター：`Form No.MM-QR-001/FM05 Ver.3-5 (2024.08.02)`（**0.節の通り版数不一致あり**、フッター文字列は編集せずそのまま保持する＝アプリが上書きしてはいけない）

ヘッダーには画像が2個（アンカー配置1、インライン配置1）あるが、内容（ロゴ等）は本解析では画像自体のバイナリまでは確認していない。Word出力時はこれらのヘッダー画像に一切触れない（テンプレートをコピーしてそのまま使うため自然に保持される）。

## 5. ブックマーク・コンテンツコントロールが無いことの設計上の意味

現行テンプレートには論理名でアクセス可能な `Bookmark` も `Content Control`（テキスト系）も存在しない。したがって：

- **Phase 3（Word出力）の初期実装は、Table/Row/Cell のインデックス直接指定で行わざるを得ない。**
- ただし、48.節の方針（Bookmark/Content Controlの論理名でアクセスする）を実現するため、**Word出力の最初の一歩として、テンプレートに対して一度だけ Bookmark を追加する「テンプレート前処理スクリプト」を用意する**ことを推奨する（後述 8.節）。これにより、次回以降のテンプレート改版でも、表位置がずれてもBookmark名でアクセスできる可能性が高まる。
- チェックボックス型コンテンツコントロールは11個あるが無名なので、出現順インデックス（0〜10）で操作するしかない。これは非常にテンプレート変更に弱い箇所であり、`fm05_v36.py` のようなバージョン別Exporterごとにインデックスをハードコードし、コメントで「どのチェックボックスに対応するか」を明記する。

## 6. FCC ID / BSMI ID の扱い（脚注）

Table 4 の脚注：
> ※1: FCC規格の場合はFCC ID番号を記入し、SDoCやDoCの記載は不要。
> ※2: CNS規格は檢磁番号又はBSMI ID（BSMIﾗﾍﾞﾙに記載）となります。

これは同一列（列5）を FCC ID と BSMI ID の両方で共用していることを意味する。`Equipment.fcc_id` と `Equipment.bsmi_id` は別フィールドとして保持し、Word出力時にどちらか入力されている方をこの列に出力する（両方入力されていれば併記）。

## 7. ケーブル上限長さの参考表（脚注）

Table 5 の脚注に、USB/LAN/RS-232C/RS485/D-sub/DVI/Display/HDMI の一般的な上限長さの目安が記載されている。これは**固定の参考情報**であり、アプリのマスタデータとして `cable_type` 選択時の参考値表示に流用できる（必須要件ではないが、入力補助として `docs/ui-design.md` のケーブル入力画面で軽く触れる）。

## 8. アプリ項目 → Word出力先 マッピング案（論理名）

Bookmark が存在しないため、以下は「将来追加するBookmark名」の提案であり、v3-6時点では実装上は Table/Row/Cell インデックスで代替する。

| 論理名 | 対応箇所 | 備考 |
|---|---|---|
| `PROJECT_NO` | Table0 R0C1 | |
| `TEST_PLAN_NO` | Table0 R1C1 | |
| `MEASUREMENT_PERIOD` | Table0 R2C1 | |
| `REPORT_STANDARD_TABLE` | Table2 R2-R9 | 可変行、行複製ロジック要 |
| `APPLICANT_BLOCK` | Table2 R10-R13 | |
| `EUT_OVERVIEW_TABLE` | Table3 全体 | A〜Qの各セルを個別Bookmark化するのが理想 |
| `EQUIPMENT_TABLE` | Table4 R3-R18 | カテゴリ別に行複製 |
| `CABLE_TABLE` | Table5 R3-R16 | 行複製 |
| `SYSTEM_DIAGRAM` | Table7 R0C0 | 画像差し替え |
| `COUNTERMEASURE_TEXT` | Table8 R1C0 | |
| `IMMUNITY_CRITERIA_TABLE` | Table9 全体 | |
| `IMMUNITY_VERIFICATION_POINTS` | Table9直後の段落群 | 段落複製 |
| `MEDICAL_CRITERIA_TABLE` | Table10 全体 | |
| `TAIWAN_APPLICANT_TABLE` | Table13 R1-R9 | |
| `TAIWAN_COMPONENT_TABLE` | Table13 R12-R26 | 行複製 |
| `TAIWAN_EUT_STATUS` | Table13 R28 | |

## 9A. 【Phase 3 実装時の追記】Word COM実測によるセル参照確定（fm05_v36）

Word Exporter実装にあたり、`python-docx`の解析だけでなく**実際にMicrosoft Word COMで文書を開いてTable/Cellのアドレス可能性を検証した**。重要な発見が2点ある。

**発見1：Word COMの`Tables`コレクションはpython-docxの`tables`と数え方が異なる。**
本文中に「試験時配置図」の表と「例)」画像の表のように、間に段落を挟まず隣接する2つの`<w:tbl>`をpython-docxは別々の表として数えるが、Word自身（COM経由）はこれを**1つの連続した表（複数行）として認識する**。そのため python-docx基準で14表だったものが、Word COM基準では13表になる。**WordExporterはCOM経由でテンブレートを操作するため、以降の行・列番号はすべてWord COM基準（1始まり）で記載する。**

**発見2：垂直結合（vMerge）された継続セルは`Table.Cell(row, col)`で例外を返す。**
これにより、結合構造を「エラーが出るかどうか」で機械的に検出できた。これを利用し、各表の結合構造を実測した。

### 確定した安全な出力先（高確度・本Phaseで実装）

| データ | Word COM位置 | 備考 |
|---|---|---|
| プロジェクト番号 | Table(1).Cell(1,2) | |
| テストプラン番号 | Table(1).Cell(2,2) | |
| 測定期間 | Table(1).Cell(3,2) | |
| レポート作成規格（最大8件） | Table(3).Cell(3..10, 3)=規格名, Cell(3..10,4)=和文/英文, Cell(3..10,5)=希望納期, Cell(3..10,6)=提出媒体 | R3〜R10の8行固定。9件目以降は行複製 |
| 装置概要 A) Kind of Equipment | Table(4).Cell(2,3) | 空欄なら上書き |
| B) Model name | Table(4).Cell(3,3) | |
| C) Serial No | Table(4).Cell(5,3) | |
| D) Operating program | Table(4).Cell(6,3) | |
| E) Type of Sample Tested | ContentControls(1)=Mass-production, ContentControls(2)=Pre-production | チェックボックス |
| F) Dimension | Table(4).Cell(9,3) | 既存プレースホルダを上書き |
| G) High Frequency Used | Table(4).Cell(10,3) | 既存ガイド文の末尾に追記（上書きしない） |
| H) Wireless frequency | Table(4).Cell(12,3) | |
| I) Rating Power Supply | ContentControls(3)=DC全体, (4)=DC 2P, (5)=DC 2P+E, (6)=1phase全体, (7)=1phase 2P, (8)=1phase 2P+E, (9)=3phase全体, (10)=3phase 3P(Δ)+E, (11)=3phase 4P(Y)+E。Table(4).Cell(13,3)へ電圧/電流値を追記 | サブ選択時は上位（全体）チェックボックスも連動してONにする |
| J) Tested Condition | Table(4).Cell(14,3) | |
| K) Date of Manufacture | Table(4).Cell(15,3) | |
| L) Manufacturer 会社名/住所 | Table(4).Cell(16,4) / Cell(17,4) | ラベルはCell(16,3)="会社名"/Cell(17,3)="住所"に既存 |
| M) Attachment | Table(4).Cell(18,3) | |
| N) Option | Table(4).Cell(19,3) | |
| P) Date of Sample Received | Table(4).Cell(23,3) | |
| Q) Test Engineer | Table(4).Cell(24,3) | |
| 機器リスト EUT(A-C) | Table(5).Cell(4-6, 2..6) | 列=Description/Model/Serial/Manufacturer/FCC・BSMI |
| 機器リスト Peripheral(D-I) | Table(5).Cell(8-13, 2..6) | 6行固定、超過時は行複製 |
| 機器リスト Associated(J-N) | Table(5).Cell(15-19, 2..6) | 5行固定、超過時は行複製 |
| ケーブルリスト（最大14本） | Table(6).Cell(4-17, 2..6) | 列=CableType/Length/Shielded/MaxLength/Outdoor |
| 構成図 | Table(7).Cell(2,1) | 「例)」記入例を消して生成画像に差し替え |
| EMC対策 | Table(8).Cell(2,1) | 既存注記の後ろに箇条書きを追記（上書きしない） |

### 未確定のため本Phaseでは出力を見送る箇所

| データ | 理由 |
|---|---|
| 申請者情報（Table(3) R11〜R14） | 各行・各列の意味（和文/英文どちらが上段か、C2列が言語ラベルなのか別項目なのか）が空欄テンプレートからは断定できない。誤った欄に転記するリスクが高いため、**実際に手入力で1件記入されたサンプルWord、または担当者への直接確認**を得てから実装する。 |
| 台湾資料（Table(13)） | 同上の理由（Table(3)の申請者情報と類似した結合構造を持つ）。C.2内部構成品リスト（R13〜R27）は列構成が明確（装置名/数量/モデル名/製造者）なため次回実装候補。 |
| 動作モード（O項目） | アプリ側に「動作モード」入力画面が未実装（Phase 1時点でプレースホルダー）のため、対応するデータソースがまだ無い。 |
| イミュニティ／医療規格 | Phase 4のスコープ。テーブル自体（Table9, Table10）は結合が単純なため実装は容易と見込まれる。 |

この方針により、**確信の持てない欄に誤ったデータを書き込むリスクを避けつつ**、確度の高い基本情報・装置概要・機器表・ケーブル表・構成図というMVPの中核部分を先行して自動出力可能にする。

## 9. テンプレート変更への耐性方針（実装ルール）

1. コード中に「Ver.3-6」等の版数文字列をハードコードしない。`TemplateDefinition` テーブルに `template_filename` / `internal_form_version`（フッターから読み取った値） / `registered_at` を保持する。
2. `exporters/word/fm05_v36.py` のように、**テンプレートを実際に開いて検証した版ごとに** Exporter ファイルを分ける。互換性がありそうでも安易に共有関数化しない（Table行数がテンプレート改版でズレた場合に、共有ロジックが両バージョンを壊すリスクを避けるため）。
3. 新しいテンプレートを受け取ったら、必ず本ドキュメントと同様の解析（本節の `analyze_docx.py` 相当のスクリプトを `tools/inspect_template.py` として整備し再利用する）を行ってから Exporter を書く。
4. Exporterは「テンプレートToken配置が変わっても、アプリ内部データモデルやDBスキーマには影響しない」ことを最優先にする（8.節の構造方針の通り）。
