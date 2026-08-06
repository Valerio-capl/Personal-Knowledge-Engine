import pytest
from src.document_loader import FileMetadata 
 
@pytest.fixture
def make_file_metadata():
    def _make(**overrides):
        defaults = dict(
            filename="sample.txt",
            filepath="/tmp/sample.txt",
            extension=".txt",
            size_bytes=100,
            page_number=1,
        )
        defaults.update(overrides)
        return FileMetadata(**defaults)
    return _make
 