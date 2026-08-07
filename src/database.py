import sqlite3
DB_PATH = "rag.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embedding_spaces (
            space_id TEXT PRIMARY KEY,
            provider_name TEXT NOT NULL,
            model_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filepath TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            space_id TEXT NOT NULL,
            last_indexed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            space_id TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def register_space(space_id, provider_name, model_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO embedding_spaces (space_id, provider_name, model_name)
        VALUES (?, ?, ?)
    """, (space_id, provider_name, model_name))
    conn.commit()
    conn.close()

def get_all_spaces():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT space_id, provider_name, model_name FROM embedding_spaces")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_file_hash(filepath):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content_hash FROM indexed_files WHERE filepath = ?", (filepath,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def upsert_file(filepath, content_hash, space_id):
    conn = get_connection()
    cursor = conn.cursor()
    # TODO: add a real last_indexed_at timestamp
    cursor.execute("""
        INSERT INTO indexed_files (filepath, content_hash, space_id, last_indexed_at)
        VALUES (?, ?, ?, NULL)
        ON CONFLICT(filepath) DO UPDATE SET
            content_hash = excluded.content_hash,
            space_id = excluded.space_id
    """, (filepath, content_hash, space_id))
    conn.commit()
    conn.close()


def add_chunks(filepath, space_id, chunk_ids):
    conn = get_connection()
    cursor = conn.cursor()
    for chunk_id in chunk_ids:
        cursor.execute("""
            INSERT OR REPLACE INTO chunks (chunk_id, filepath, space_id)
            VALUES (?, ?, ?)
        """, (chunk_id, filepath, space_id))
    conn.commit()
    conn.close()


def get_chunk_ids_for_file(filepath, space_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chunk_id FROM chunks WHERE filepath = ? AND space_id = ?", (filepath, space_id))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def delete_chunks_for_file(filepath, space_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chunks WHERE filepath = ? AND space_id = ?", (filepath, space_id))
    conn.commit()
    conn.close()
    # FIXME: delete the actual vectors from the VectorStore separately