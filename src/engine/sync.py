from pathlib import Path
from document.factory import DocumentLoaderFactory
from document.exceptions import UnsupportedFormatError
from document.splitter import RecursiveCharacterTextSplitter, MarkdownAwareTextSplitter

def sync_folder(base_folder, space, vector_space_manager, database):
    base_folder = Path(base_folder)

    for file_path in base_folder.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            loader = DocumentLoaderFactory.get_loader(file_path)
        except UnsupportedFormatError:
            # not a supported extension skip
            continue

        current_hash = loader._content_hash
        old_hash = database.get_file_hash(str(file_path))
        if old_hash == current_hash:
            continue

        documents = loader.load()
        if file_path.suffix.lower() == ".md":
            splitter = MarkdownAwareTextSplitter()
        else:
            splitter = RecursiveCharacterTextSplitter()

        chunks = []
        for doc in documents:
            chunks.extend(splitter.split(doc))

        # TODO: if chunks is empty
        if chunks:
            vector_space_manager.index_chunks(space, chunks)

        database.upsert_file(str(file_path), current_hash, space.space_id)