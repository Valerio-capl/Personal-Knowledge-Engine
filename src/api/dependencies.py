from dotenv import load_dotenv

load_dotenv()

from database.db import Database
from engine.space_manager import VectorSpaceManager

# created once when the app starts
db = Database("rag.db")
vsm = VectorSpaceManager(storage_dir="vector_spaces", database=db)