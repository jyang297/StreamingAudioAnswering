"""Characterization/spike tests of the SQLite execution boundary, without endpoints."""
import asyncio
from dataclasses import FrozenInstanceError
import sqlite3
import threading

import pytest

from multitable_poc.database import SQLiteCatalog
from multitable_poc.models import ContractError, Plan, Query


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE members (id INTEGER PRIMARY KEY, team_id INTEGER REFERENCES teams(id), "full name" TEXT, score REAL);
            INSERT INTO teams VALUES (1,'Alpha'),(2,'Beta');
            INSERT INTO members VALUES (10,1,'Ada',7),(11,1,'Lin',9),(12,2,'Jo',4);
        ''')
    return path


def test_schema_original_sql_and_database_identity(database):
    catalog = SQLiteCatalog(database, "fixture")
    query = catalog.validate('SELECT m."full name", t.name FROM members m JOIN teams t ON m.team_id=t.id;')
    assert query.sql.endswith(';')
    assert query.json() == {"sql": query.sql, "db_id": "fixture", "schema_id": catalog.schema_id}
    assert len(catalog.schema_payload['tables']) == 2
    assert catalog.schema_payload['tables'][0]['foreign_keys'][0]['table'] == 'teams'
    assert query != Query(query.sql, "another", query.schema_id)
    exposed = catalog.schema_payload
    exposed['tables'].clear()
    assert len(catalog.schema_payload['tables']) == 2
    with pytest.raises(FrozenInstanceError):
        query.sql = 'DELETE FROM teams'
    assert Plan.parse({'action': 'retrieve', 'query': {'sql': query.sql}}, catalog).query == query
    assert Plan.parse({'action': 'wait', 'query': None}, catalog) == Plan('wait', None)
    with pytest.raises(ContractError):
        Plan.parse({'action':'retrieve','query':query.json()}, catalog)


@pytest.mark.parametrize('sql, expected', [
    ('SELECT "full name" FROM members ORDER BY id', [['Ada'],['Lin'],['Jo']]),
    ('SELECT COUNT(*) FROM teams', [[2]]),
    ('WITH ids AS (SELECT team_id FROM members), grouped AS (SELECT team_id FROM ids GROUP BY team_id) SELECT COUNT(*) FROM grouped', [[2]]),
    ('SELECT t.id, m.id FROM teams t JOIN members m ON t.id=m.team_id ORDER BY m.id', [[1,10],[1,11],[2,12]]),
    ('WITH s AS (SELECT team_id, SUM(score) AS total FROM members GROUP BY team_id) SELECT t.name, s.total FROM s JOIN teams t ON s.team_id=t.id ORDER BY t.id', [['Alpha',16.0],['Beta',4.0]]),
    ('SELECT name FROM teams t WHERE EXISTS (SELECT 1 FROM members m WHERE m.team_id=t.id AND score>8)', [['Alpha']]),
    ('SELECT name FROM teams WHERE id IN (SELECT team_id FROM members WHERE score>8)', [['Alpha']]),
    ('SELECT name FROM teams WHERE id=1 UNION SELECT "full name" FROM members WHERE id=12 ORDER BY 1', [['Alpha'],['Jo']]),
    ('SELECT name FROM (SELECT name FROM teams WHERE id=1) x', [['Alpha']]),
])
async def test_real_multitable_scope_and_duplicate_columns(database, sql, expected):
    catalog = SQLiteCatalog(database, 'fixture')
    try:
        rows = await catalog.search(catalog.validate(sql))
        assert [row['values'] for row in rows] == expected
        if sql.startswith('SELECT t.id'):
            assert rows[0]['columns'] == ['id','id']
        assert catalog.metrics[-1]['status'] == 'ok'
        assert catalog.metrics[-1]['elapsed_ms'] >= 0
    finally:
        await catalog.close()


@pytest.mark.parametrize('sql', [
    'SELECT * FROM teams; DELETE FROM teams',
    'WITH x AS (DELETE FROM teams RETURNING *) SELECT * FROM x',
    'ATTACH DATABASE ":memory:" AS another',
    'PRAGMA table_info(teams)',
    'SELECT * FROM temp.teams',
    'SELECT * FROM other.teams',
    'SELECT * FROM sqlite_master',
    "SELECT load_extension('anything')",
    "SELECT readfile('/etc/passwd')",
    'SELECT * FROM pragma_table_info("teams")',
    'SELECT randomblob(100000000)',
    'SELECT * FROM members WHERE id=?',
    'SELECT * FROM members WHERE id=:id',
    'SELECT missing FROM teams',
    'SELECT "definitely_unknown_column" FROM teams',
    'SELECT name FROM teams WHERE name = "definitely_unknown_column"',
    'SELECT t.missing FROM teams t',
    'SELECT id FROM teams t JOIN members m ON t.id=m.team_id',
    'WITH x AS (SELECT id FROM teams) SELECT name FROM x',
    'WITH sqlite_master AS (SELECT 1) SELECT COUNT(*) FROM main.sqlite_master',
])
def test_side_effects_catalog_escapes_and_bad_scope_rejected(database, sql):
    with pytest.raises(ContractError):
        SQLiteCatalog(database, 'fixture').validate(sql)


async def test_execution_revalidates_forged_query_and_scope(database):
    catalog = SQLiteCatalog(database, 'fixture')
    safe = catalog.validate('SELECT name FROM teams')
    for query in (Query(safe.sql,'other',safe.schema_id), Query(safe.sql,safe.db_id,'stale'),
                  Query('DELETE FROM teams',safe.db_id,safe.schema_id),
                  Query('SELECT * FROM sqlite_master',safe.db_id,safe.schema_id)):
        with pytest.raises(ContractError):
            await catalog.search(query)
    assert len(await catalog.search(safe)) == 2
    await catalog.close()


async def test_empty_result_is_success_and_limits_are_failures(database):
    catalog = SQLiteCatalog(database, 'fixture', max_rows=1)
    assert await catalog.search(catalog.validate('SELECT * FROM teams WHERE id=999')) == []
    assert catalog.metrics[-1]['status'] == 'ok'
    with pytest.raises(ContractError, match='row bound'):
        await catalog.search(catalog.validate('SELECT name FROM teams'))
    assert catalog.metrics[-1]['status'] == 'error'
    await catalog.close()
    bounded = SQLiteCatalog(database, 'fixture', max_result_bytes=350)
    sql = "SELECT replace(replace(name,'a','aaaaaaaaaa'),'a','aaaaaaaaaa') FROM teams"
    with pytest.raises(ContractError):
        await bounded.search(bounded.validate(sql))
    await bounded.close()


async def test_cancel_stops_sqlite_worker_and_next_query_runs(database, monkeypatch):
    catalog = SQLiteCatalog(database, 'fixture', timeout_s=5)
    prepared = threading.Event()
    original = catalog._prepare
    def observe_prepare(*args):
        original(*args)
        prepared.set()
    query = catalog.validate('WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<1000000000) SELECT SUM(x) FROM n')
    monkeypatch.setattr(catalog, '_prepare', observe_prepare)
    task = asyncio.create_task(catalog.search(query))
    assert await asyncio.to_thread(prepared.wait, 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 1)
    assert not catalog._active
    assert catalog.metrics[-1]['status'] == 'cancelled'
    assert len(await catalog.search(catalog.validate('SELECT * FROM teams'))) == 2
    await catalog.close()


async def test_deadline_and_close_drain_real_workers(database):
    catalog = SQLiteCatalog(database, 'fixture', timeout_s=0.03)
    query = catalog.validate('WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<1000000000) SELECT SUM(x) FROM n')
    with pytest.raises(TimeoutError):
        await catalog.search(query)
    assert not catalog._active
    catalog.timeout_s = 5
    task = asyncio.create_task(catalog.search(query))
    await asyncio.sleep(0.01)
    await asyncio.wait_for(catalog.close(), 1)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not catalog._active
    with pytest.raises(ContractError, match='closed'):
        catalog.validate('SELECT * FROM teams')


def test_descriptions_change_identity_and_ddl_changes_invalidate_query(database, tmp_path):
    descriptions = tmp_path / 'descriptions'
    descriptions.mkdir()
    file = descriptions / 'teams.csv'
    file.write_text('original_column_name,column_description\nname,Team label\n')
    first = SQLiteCatalog(database, 'fixture', description_dir=descriptions)
    file.write_text('original_column_name,column_description\nname,Published team label\n')
    second = SQLiteCatalog(database, 'fixture', description_dir=descriptions)
    assert first.schema_id != second.schema_id
    with sqlite3.connect(database) as conn:
        conn.execute('ALTER TABLE teams ADD COLUMN region TEXT')
    with pytest.raises(ContractError, match='schema changed'):
        first.validate('SELECT * FROM teams')


def test_virtual_tables_are_not_ordinary_catalog_tables(database):
    with sqlite3.connect(database) as conn:
        try:
            conn.execute('CREATE\nVIRTUAL TABLE text_index USING fts5(body)')
        except sqlite3.OperationalError as exc:
            if 'no such module' in str(exc):
                pytest.skip('this SQLite build does not include FTS5')
            raise
    with pytest.raises(ContractError, match='virtual tables'):
        SQLiteCatalog(database, 'fixture')


def test_cte_cannot_impersonate_excluded_view(database):
    with sqlite3.connect(database) as conn:
        conn.execute('CREATE VIEW hidden AS SELECT id FROM teams')
    catalog = SQLiteCatalog(database, 'fixture')
    with pytest.raises(ContractError):
        catalog.validate('WITH hidden AS (SELECT 1) SELECT COUNT(*) FROM main.hidden')


def test_runtime_without_dqs_configuration_fails_closed(database, monkeypatch):
    monkeypatch.delattr(sqlite3, 'SQLITE_DBCONFIG_DQS_DML')
    with pytest.raises(ContractError, match='Python 3.12.*DQS_DML'):
        SQLiteCatalog(database, 'fixture')
