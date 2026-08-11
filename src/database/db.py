import sqlite3
from contextlib import contextmanager
from pathlib import Path
from database.exceptions import DatabaseError

DEFAULT_DB_PATH = "rag.db"

class Database:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"query failed: {e}") from e
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_spaces (
                    space_id TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    model_name TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS indexed_files (
                    filepath TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    space_id TEXT NOT NULL,
                    last_indexed_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    filepath TEXT NOT NULL,
                    space_id TEXT NOT NULL
                )
            """)

    def register_space(self, space_id: str, provider_name: str, model_name: str) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO embedding_spaces (space_id, provider_name, model_name)
                VALUES (?, ?, ?)
            """, (space_id, provider_name, model_name))

    def get_all_spaces(self) -> list[tuple[str, str, str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT space_id, provider_name, model_name FROM embedding_spaces").fetchall()
        return [(row["space_id"], row["provider_name"], row["model_name"]) for row in rows]

    def get_file_hash(self, filepath:str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT content_hash FROM indexed_files WHERE filepath = ?", (filepath,)
            ).fetchone()
        return row["content_hash"] if row else None

    def upsert_file(self, filepath: str, content_hash: str, space_id: str) -> None:
        # TODO: add a real last_indexed_at timestamp
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO indexed_files (filepath, content_hash, space_id, last_indexed_at)
                VALUES (?, ?, ?, NULL)
                ON CONFLICT(filepath) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    space_id = excluded.space_id
            """, (filepath, content_hash, space_id))

    def add_chunks(self, filepath: str, space_id: str, chunk_ids: list[str]) -> None:
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO chunks (chunk_id, filepath, space_id) VALUES (?, ?, ?)",
                [(chunk_id, filepath, space_id) for chunk_id in chunk_ids],
            )

    def get_chunk_ids_for_file(self, filepath: str, space_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT chunk_id FROM chunks WHERE filepath = ? AND space_id = ?",
                (filepath, space_id),
            ).fetchall()
        return [row["chunk_id"] for row in rows]



    def delete_chunks_for_file(self, filepath: str, space_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM chunks WHERE filepath = ? AND space_id = ?", (filepath, space_id)
            )

        # FIXME: delete the actual vectors from the VectorStore separately