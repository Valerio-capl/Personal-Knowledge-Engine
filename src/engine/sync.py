from pathlib import Path
from dataclasses import dataclass, field

from database.db import Database
from document.factory import DocumentLoaderFactory
from document.exceptions import UnsupportedFormatError, DocumentLoaderError
from document.loader import DocumentLoader
from document.splitter import RecursiveCharacterTextSplitter, MarkdownAwareTextSplitter, TextSplitter
from embedding.exceptions import EmbeddingError
from engine.exceptions import FileSyncError
from engine.space_manager import EmbeddingSpaceConfig, VectorSpaceManager
from vector_store.exceptions import VectorStoreError

@dataclass
class SyncReport:
    """outcome of a single sync run."""
    synced: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return len(self.synced) + len(self.skipped) + len(self.failed)

class SyncEngine:
    def __init__(self, database: Database, vector_space_manager: VectorSpaceManager):
        self._db = database
        self._vsm = vector_space_manager

    def sync_folder(self, base_folder:str | Path, space: EmbeddingSpaceConfig) -> SyncReport:
        base_folder = self._validate_folder(base_folder)
        report = SyncReport()
        
        for file_path in base_folder.rglob("*"):
            if not file_path.is_file():
                continue
            self._sync_file(file_path, space, report)
        return report

    def _sync_file(self, file_path: Path, space: EmbeddingSpaceConfig, report:SyncReport) -> None:
        try:
            loader = DocumentLoaderFactory.get_loader(file_path)
        except UnsupportedFormatError:
            report.skipped.append(str(file_path))
            return

        current_hash = loader.content_hash
        old_hash = self._db.get_file_hash(str(file_path))
        if old_hash == current_hash:
            report.skipped.append(str(file_path))
            return
        try:            
            if old_hash is not None:
                self._remove_old_chunks(file_path, space)
            self._index_file(loader, file_path, space, current_hash)
            report.synced.append(str(file_path))
        except FileSyncError as e:
            report.failed.append((str(file_path), str(e)))
            # TODO: add logging here warning

    def _index_file(
        self,
        loader: DocumentLoader,
        file_path: Path,
        space: EmbeddingSpaceConfig,
        content_hash: str,
    ) -> None:
        try:
            documents = loader.load()
        except DocumentLoaderError as e:
            raise FileSyncError(f"failed to load {file_path}: {e}") from e
        
        splitter = self._get_splitter(file_path)
        chunks = [chunk for doc in documents for chunk in splitter.split(doc)]

        try:
            # TODO: if chunks is empty
            if chunks:
                self._vsm.index_chunks(space, chunks)
            self._db.upsert_file(str(file_path), content_hash, space.space_id)
        except (EmbeddingError, VectorStoreError) as e:
            raise FileSyncError(f"failed to index {file_path}: {e}") from e

    def _remove_old_chunks(self, file_path: Path, space: EmbeddingSpaceConfig) -> None:
        old_chunk_ids = self._db.get_chunk_ids_for_file(str(file_path), space.space_id)
        if old_chunk_ids:
            self._vsm.delete_chunks(space, old_chunk_ids)
        self._db.delete_chunks_for_file(str(file_path), space.space_id)

    @staticmethod
    def _get_splitter(file_path:Path) -> TextSplitter:
        if file_path.suffix.lower() == ".md":
            return MarkdownAwareTextSplitter()
        return RecursiveCharacterTextSplitter()
    
    @staticmethod
    def _validate_folder(base_folder: str | Path) -> Path:
        path = Path(base_folder)
        if not path.exists():
            raise FileNotFoundError(f"Folder not found: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        return path