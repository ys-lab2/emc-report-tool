-- docs/database-schema.md に対応する初期スキーマ

CREATE TABLE projects (
    project_id              TEXT PRIMARY KEY,
    project_no              TEXT,
    test_plan_no             TEXT,
    measurement_period       TEXT,
    include_immunity         INTEGER NOT NULL DEFAULT 0,
    include_medical          INTEGER NOT NULL DEFAULT 0,
    include_taiwan           INTEGER NOT NULL DEFAULT 0,
    notes                     TEXT,
    created_at                TEXT NOT NULL,
    updated_at                TEXT NOT NULL
);

CREATE TABLE template_definitions (
    template_definition_id     TEXT PRIMARY KEY,
    project_id                  TEXT NOT NULL UNIQUE REFERENCES projects(project_id) ON DELETE CASCADE,
    template_id                 TEXT NOT NULL,
    template_version             TEXT NOT NULL,
    template_internal_version    TEXT,
    template_filename            TEXT NOT NULL,
    registered_at                 TEXT NOT NULL
);

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
    rating_power_supply_types      TEXT,
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

CREATE TABLE equipments (
    equipment_id       TEXT PRIMARY KEY,
    project_id           TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    display_id             TEXT NOT NULL,
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

CREATE TABLE countermeasures (
    countermeasure_id     TEXT PRIMARY KEY,
    project_id               TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    description                TEXT,
    component_model              TEXT,
    component_manufacturer         TEXT,
    sort_order                       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_countermeasures_project ON countermeasures(project_id);

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

CREATE TABLE diagram_nodes (
    node_id           TEXT PRIMARY KEY,
    project_id          TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    ref_type              TEXT NOT NULL CHECK(ref_type IN ('Equipment','PowerSource','GroundConnection')),
    ref_id                  TEXT NOT NULL,
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
    ref_id                TEXT NOT NULL,
    route_points_json      TEXT,
    label_dx                 REAL NOT NULL DEFAULT 0,
    label_dy                   REAL NOT NULL DEFAULT 0
);
CREATE INDEX idx_diagram_edges_project ON diagram_edges(project_id);
CREATE UNIQUE INDEX idx_diagram_edges_ref ON diagram_edges(project_id, ref_type, ref_id);

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
