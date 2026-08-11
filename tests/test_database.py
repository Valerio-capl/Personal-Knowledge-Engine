import pytest
from database.db import Database

@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")

def test_database_creates_file_on_init(tmp_path):
    db_path = tmp_path / "fresh.db"
    Database(db_path)
    assert db_path.exists()

def test_init_schema_is_idempotent(tmp_path):
    db_path = tmp_path / "fresh.db"
    Database(db_path)
    Database(db_path)


def test_register_space_and_get_all_spaces(db):
    db.register_space("space_1", "openai", "text-embedding-3-small")
    spaces = db.get_all_spaces()
    assert spaces == [("space_1", "openai", "text-embedding-3-small")]


def test_register_space_is_idempotent_on_same_id(db):
    db.register_space("space_1", "openai", "text-embedding-3-small")
    db.register_space("space_1", "openai", "text-embedding-3-small")
    assert len(db.get_all_spaces()) == 1


def test_get_all_spaces_returns_empty_list_when_none_registered(db):
    assert db.get_all_spaces() == []


def test_get_file_hash_returns_none_for_unknown_file(db):
    assert db.get_file_hash("/tmp/does_not_exist.txt") is None


def test_upsert_file_then_get_file_hash_returns_stored_hash(db):
    db.upsert_file("/tmp/note.txt", "hash_v1", "space_1")
    assert db.get_file_hash("/tmp/note.txt") == "hash_v1"


def test_upsert_file_updates_hash_on_conflict(db):
    db.upsert_file("/tmp/note.txt", "hash_v1", "space_1")
    db.upsert_file("/tmp/note.txt", "hash_v2", "space_1")
    assert db.get_file_hash("/tmp/note.txt") == "hash_v2"


def test_upsert_file_updates_space_id_on_conflict(db):
    db.upsert_file("/tmp/note.txt", "hash_v1", "space_1")
    db.upsert_file("/tmp/note.txt", "hash_v1", "space_2")
    assert db.get_file_hash("/tmp/note.txt") == "hash_v1"



def test_add_chunks_and_get_chunk_ids_for_file(db):
    db.add_chunks("/tmp/note.txt", "space_1", ["c1", "c2", "c3"])
    chunk_ids = db.get_chunk_ids_for_file("/tmp/note.txt", "space_1")
    assert sorted(chunk_ids) == ["c1", "c2", "c3"]

def test_get_chunk_ids_for_file_returns_empty_list_when_none(db):
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_1") == []


def test_add_chunks_scoped_by_space_id(db):
    db.add_chunks("/tmp/note.txt", "space_1", ["c1"])
    db.add_chunks("/tmp/note.txt", "space_2", ["c2"])
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_1") == ["c1"]
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_2") == ["c2"]


def test_add_chunks_replaces_on_conflicting_chunk_id(db):
    db.add_chunks("/tmp/note.txt", "space_1", ["c1"])
    db.add_chunks("/tmp/other.txt", "space_1", ["c1"])
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_1") == []
    assert db.get_chunk_ids_for_file("/tmp/other.txt", "space_1") == ["c1"]


def test_delete_chunks_for_file_removes_matching_rows(db):
    db.add_chunks("/tmp/note.txt", "space_1", ["c1", "c2"])
    db.delete_chunks_for_file("/tmp/note.txt", "space_1")
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_1") == []


def test_delete_chunks_for_file_is_scoped_by_space_id(db):
    db.add_chunks("/tmp/note.txt", "space_1", ["c1"])
    db.add_chunks("/tmp/note.txt", "space_2", ["c2"])
    db.delete_chunks_for_file("/tmp/note.txt", "space_1")
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_1") == []
    assert db.get_chunk_ids_for_file("/tmp/note.txt", "space_2") == ["c2"]


def test_delete_chunks_for_file_on_nonexistent_file_is_noop(db):
    db.delete_chunks_for_file("/tmp/never_indexed.txt", "space_1")