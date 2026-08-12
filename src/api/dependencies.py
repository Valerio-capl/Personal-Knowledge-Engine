from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

from database.db import Database
from engine.space_manager import VectorSpaceManager
from engine.sync import SyncEngine

# created once when the app starts
DB_PATH = "rag.db"
VECTOR_SPACES_DIR = "vector_spaces"

@lru_cache
def get_database() -> Database:
    return Database(DB_PATH)

@lru_cache
def get_vector_space_manager() -> VectorSpaceManager:
    return VectorSpaceManager(storage_dir=VECTOR_SPACES_DIR, database=get_database())

def get_sync_engine() -> SyncEngine:
    return SyncEngine(database=get_database(), vector_space_manager=get_vector_space_manager())