import pytest
from document.loader import FileMetadata 
 
@pytest.fixture
def make_file_metadata():
    def _make(**overrides):
        defaults = dict(
            filename="sample.txt",
            filepath="/tmp/sample.txt",
            extension=".txt",
            size_bytes=100,
            page_number=1,
            content_hash="fakehash1234567890abcdef"
        )
        defaults.update(overrides)
        return FileMetadata(**defaults)
    return _make
 