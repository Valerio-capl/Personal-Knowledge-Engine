import pytest

from database.db import Database
from embedding.exceptions import EmbeddingAPIError
from engine.space_manager import EmbeddingSpaceConfig
from engine.sync import SyncEngine


class _FakeVectorSpaceManager:
    def __init__(self):
        self.indexed_chunks = []
        self.deleted = []
        self.persisted = []

    def index_chunks(self, space, chunks):
        self.indexed_chunks.append((space, chunks))

    def delete_chunks(self, space, chunk_ids):
        self.deleted.append((space, chunk_ids))

    def persist(self, space):
        self.persisted.append(space)


class _FailingOnFilenameVectorSpaceManager(_FakeVectorSpaceManager):
    def __init__(self, fail_if_contains):
        super().__init__()
        self._fail_if_contains = fail_if_contains

    def index_chunks(self, space, chunks):
        filepath = chunks[0].source_metadata.filepath
        if self._fail_if_contains in filepath:
            raise EmbeddingAPIError("simulated failure")
        super().index_chunks(space, chunks)


SPACE = EmbeddingSpaceConfig(provider_name="ollama", model_name="fake-model")

@pytest.fixture
def db(tmp_path):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    return Database(db_dir / "test.db")

@pytest.fixture
def docs_dir(tmp_path):
    path = tmp_path / "docs"
    path.mkdir()
    return path


def test_sync_indexes_new_file(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    file_path = docs_dir / "note.txt"
    file_path.write_text("some content to index")
    report = engine.sync(docs_dir, SPACE)

    assert report.synced == [str(file_path)]
    assert report.skipped == []
    assert report.failed == []
    assert len(vsm.indexed_chunks) == 1
    assert db.get_file_hash(str(file_path)) is not None
    assert vsm.persisted == [SPACE]


def test_sync_skips_unchanged_file_on_second_run(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    file_path = docs_dir / "note.txt"
    file_path.write_text("unchanged content")
    engine.sync(docs_dir, SPACE)
    report = engine.sync(docs_dir, SPACE)

    assert report.skipped == [str(file_path)]
    assert report.synced == []
    assert len(vsm.indexed_chunks) == 1  # not re-indexed


def test_sync_reindexes_modified_file_and_removes_stale_chunks(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    file_path = docs_dir / "note.txt"
    file_path.write_text("original content")

    engine.sync(docs_dir, SPACE)
    db.add_chunks(str(file_path), SPACE.space_id, ["old_chunk_1", "old_chunk_2"])
    file_path.write_text("completely different content now")
    report = engine.sync(docs_dir, SPACE)

    assert report.synced == [str(file_path)]
    assert vsm.deleted == [(SPACE, ["old_chunk_1", "old_chunk_2"])]
    assert db.get_chunk_ids_for_file(str(file_path), SPACE.space_id) == []


def test_sync_skips_unsupported_extension(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    file_path = docs_dir / "note.xyz"
    file_path.write_text("unsupported format")
    report = engine.sync(docs_dir, SPACE)

    assert report.skipped == [str(file_path)]
    assert vsm.indexed_chunks == []


def test_sync_continues_after_a_file_fails(db, docs_dir):
    vsm = _FailingOnFilenameVectorSpaceManager(fail_if_contains="bad")
    engine = SyncEngine(db, vsm)
    good_file = docs_dir / "good.txt"
    good_file.write_text("this one indexes fine")
    bad_file = docs_dir / "bad.txt"
    bad_file.write_text("this one fails during indexing")
    report = engine.sync(docs_dir, SPACE)

    assert str(good_file) in report.synced
    assert any(f == str(bad_file) for f, _ in report.failed)
    assert db.get_file_hash(str(bad_file)) is None


def test_sync_raises_for_missing_folder(db, tmp_path):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    with pytest.raises(FileNotFoundError):
        engine.sync(tmp_path / "does_not_exist", SPACE)


def test_sync_raises_when_folder_is_actually_a_file(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    not_a_folder = docs_dir / "note.txt"
    not_a_folder.write_text("just a file")
    with pytest.raises(NotADirectoryError):
        engine.sync(not_a_folder, SPACE)


def test_sync_removes_chunks_for_deleted_files(db, docs_dir):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    file_path = docs_dir / "note.txt"
    file_path.write_text("some content")
    engine.sync(docs_dir, SPACE)
    db.add_chunks(str(file_path), SPACE.space_id, ["chunk_1", "chunk_2"])
    file_path.unlink()
    report = engine.sync(docs_dir, SPACE)

    assert report.deleted == [str(file_path)]
    assert vsm.deleted == [(SPACE, ["chunk_1", "chunk_2"])]
    assert db.get_file_hash(str(file_path)) is None
    assert db.get_chunk_ids_for_file(str(file_path), SPACE.space_id) == []


def test_sync_does_not_delete_files_tracked_outside_the_synced_folder(db, docs_dir, tmp_path):
    vsm = _FakeVectorSpaceManager()
    engine = SyncEngine(db, vsm)
    other_folder = tmp_path / "other_docs"
    other_folder.mkdir()
    other_file = other_folder / "external.txt"
    db.upsert_file(str(other_file.resolve()), "some_hash", SPACE.space_id)
    db.add_chunks(str(other_file.resolve()), SPACE.space_id, ["external_chunk"])
    report = engine.sync(docs_dir, SPACE)
    assert report.deleted == []
    assert vsm.deleted == []