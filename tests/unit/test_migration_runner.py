import sqlite3

from database.migration_runner import apply_migrations

EXPECTED_TABLES = {
    "schema_migrations",
    "projects",
    "template_definitions",
    "applicants",
    "report_standards",
    "eut_overviews",
    "frequencies",
    "operation_modes",
    "equipments",
    "countermeasures",
    "cables",
    "inline_components",
    "power_sources",
    "ground_connections",
    "diagram_nodes",
    "diagram_edges",
    "immunity_criteria",
    "immunity_verification_points",
    "medical_criteria",
    "medical_criteria_items",
    "taiwan_applicants",
    "taiwan_factories",
    "internal_components",
    "import_sources",
    "import_candidates",
}


def test_apply_migrations_creates_all_tables():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    applied = apply_migrations(conn)
    assert applied == [1, 2]

    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {row["name"] for row in rows}

    assert EXPECTED_TABLES.issubset(table_names)


def test_apply_migrations_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    first = apply_migrations(conn)
    second = apply_migrations(conn)

    assert first == [1, 2]
    assert second == []


def test_equipment_self_parent_check_constraint():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    apply_migrations(conn)

    conn.execute(
        "INSERT INTO projects (project_id, created_at, updated_at) VALUES ('p1','t','t')"
    )
    conn.execute(
        """
        INSERT INTO equipments
            (equipment_id, project_id, display_id, category, placement_type, created_at, updated_at)
        VALUES ('e1','p1','A','EUT','standalone','t','t')
        """
    )

    try:
        conn.execute(
            "UPDATE equipments SET parent_equipment_id = 'e1' WHERE equipment_id = 'e1'"
        )
        assert False, "self-parent should violate CHECK constraint"
    except sqlite3.IntegrityError:
        pass
