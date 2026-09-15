-- Equipment に寸法（EUT毎のWidth/Depth/Height）を追加
ALTER TABLE equipments ADD COLUMN width_mm REAL;
ALTER TABLE equipments ADD COLUMN depth_mm REAL;
ALTER TABLE equipments ADD COLUMN height_mm REAL;

-- PowerSource に周波数・試験電圧を追加（kindにCVCFを許容するようCHECK制約を緩和）
ALTER TABLE power_sources ADD COLUMN frequency_hz TEXT;
ALTER TABLE power_sources ADD COLUMN test_voltage TEXT;

CREATE TABLE power_sources_new (
    power_source_id  TEXT PRIMARY KEY,
    project_id         TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    kind                 TEXT NOT NULL CHECK(kind IN
                           ('AC100V','AC200V','DC24V','CommercialAC','StabilizedPowerSupply','ACPowerSupply','DCPowerSupply','CVCF','Other')),
    label                  TEXT,
    notes                    TEXT,
    frequency_hz               TEXT,
    test_voltage                 TEXT
);
INSERT INTO power_sources_new (power_source_id, project_id, kind, label, notes, frequency_hz, test_voltage)
SELECT power_source_id, project_id, kind, label, notes, frequency_hz, test_voltage FROM power_sources;
DROP TABLE power_sources;
ALTER TABLE power_sources_new RENAME TO power_sources;

-- Cable の接続先を Equipment だけでなく PowerSource / GroundConnection にも接続できるよう汎用化する。
-- diagram_nodes.ref_type/ref_id と同じ考え方（多態的参照のためFK制約は付与せず、整合性はService層で担保）。
CREATE TABLE cables_new (
    cable_id            TEXT PRIMARY KEY,
    project_id            TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    cable_no                INTEGER NOT NULL,
    from_ref_type             TEXT NOT NULL DEFAULT 'Equipment' CHECK(from_ref_type IN ('Equipment','PowerSource','GroundConnection')),
    from_ref_id                 TEXT NOT NULL,
    from_port                     TEXT,
    to_ref_type                     TEXT NOT NULL DEFAULT 'Equipment' CHECK(to_ref_type IN ('Equipment','PowerSource','GroundConnection')),
    to_ref_id                         TEXT NOT NULL,
    to_port                             TEXT,
    cable_type                           TEXT,
    length                                 REAL,
    length_unit                             TEXT DEFAULT 'm',
    shielded                                 TEXT CHECK(shielded IN ('shielded','non_shielded','unknown')) DEFAULT 'unknown',
    maximum_length                            TEXT,
    outdoor_connection                         TEXT CHECK(outdoor_connection IN ('yes','no','unknown')) DEFAULT 'unknown',
    notes                                        TEXT,
    sort_order                                    INTEGER NOT NULL DEFAULT 0,
    created_at                                      TEXT NOT NULL,
    updated_at                                      TEXT NOT NULL
);
INSERT INTO cables_new
    (cable_id, project_id, cable_no, from_ref_type, from_ref_id, from_port, to_ref_type, to_ref_id, to_port,
     cable_type, length, length_unit, shielded, maximum_length, outdoor_connection, notes, sort_order, created_at, updated_at)
SELECT
    cable_id, project_id, cable_no, 'Equipment', from_equipment_id, from_port, 'Equipment', to_equipment_id, to_port,
    cable_type, length, length_unit, shielded, maximum_length, outdoor_connection, notes, sort_order, created_at, updated_at
FROM cables;
DROP TABLE cables;
ALTER TABLE cables_new RENAME TO cables;
CREATE INDEX idx_cables_project ON cables(project_id);
CREATE INDEX idx_cables_from ON cables(from_ref_type, from_ref_id);
CREATE INDEX idx_cables_to ON cables(to_ref_type, to_ref_id);
