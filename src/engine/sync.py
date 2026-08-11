from pathlib import Path
from document.factory import DocumentLoaderFactory
from document.exceptions import UnsupportedFormatError
from document.splitter import RecursiveCharacterTextSplitter, MarkdownAwareTextSplitter

class SyncEngine:
    def __init__(self, database, vector_space_manager):
        self._db = database
        self._vsm = vector_space_manager

    def sync_folder(self, base_folder, space):
        base_folder = Path(base_folder)
        if not base_folder.exists():
            raise FileNotFoundError(f"Folder not found: {base_folder}")
        if not base_folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {base_folder}")
        
        for file_path in base_folder.rglob("*"):
            if not file_path.is_file():
                continue
            self._sync_file(file_path, space)

    def _sync_file(self, file_path, space):
        try:
            loader = DocumentLoaderFactory.get_loader(file_path)
        except UnsupportedFormatError:
            # not a supported extension skip
            return

        current_hash = loader._content_hash
        old_hash = self._db.get_file_hash(str(file_path))
        if old_hash == current_hash:
            return
        if old_hash is not None:
            self._remove_old_chunks(file_path, space)

        documents = loader.load()
        splitter = self._get_splitter(file_path)

        chunks = []
        for doc in documents:
            chunks.extend(splitter.split(doc))

        # TODO: if chunks is empty
        if chunks:
            self._vsm.index_chunks(space, chunks)
        self._db.upsert_file(str(file_path), current_hash, space.space_id)

    def _remove_old_chunks(self, file_path, space):
        old_chunk_ids = self._db.get_chunk_ids_for_file(str(file_path), space.space_id)
        if old_chunk_ids:
            self._vsm.delete_chunks(space, old_chunk_ids)
        self._db.delete_chunks_for_file(str(file_path), space.space_id)

    @staticmethod
    def _get_splitter(file_path):
        if file_path.suffix.lower() == ".md":
            return MarkdownAwareTextSplitter()
        return RecursiveCharacterTextSplitter()