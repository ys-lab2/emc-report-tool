import sqlite3

import pytest

from database.migration_runner import apply_migrations
from models.project import Project
from repositories import project_repository
from utils.time_utils import now_iso
from utils.uuid_utils import new_id


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    apply_migrations(connection)
    yield connection
    connection.close()


@pytest.fixture
def project(conn):
    timestamp = now_iso()
    p = Project(project_id=new_id(), created_at=timestamp, updated_at=timestamp)
    project_repository.insert(conn, p)
    return p
