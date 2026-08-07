import re
import pytest
import tiktoken

from document.loader import LoadedDocument
from document.splitter import (
	Chunk,
	InvalidChunkConfigError,
	RecursiveCharacterTextSplitter,
	MarkdownAwareTextSplitter,
)

# mock del tokenizer
class _FakeEncoding:
	"""Mock and deterministic encoder"""
	def encode(self, text, disallowed_special=()):
		return re.findall(r"\w+|[^\w\s]", text)

_KNOWN_ENCODINGS = {"cl100k_base", "o200k_base", "p50k_base", "r50k_base"}


@pytest.fixture(autouse=True)
def mock_tiktoken(monkeypatch):
	def _fake_get_encoding(name):
		# Replicates real tiktoken behavior.
		if name not in _KNOWN_ENCODINGS:
			raise ValueError(f"Unknown encoding {name!r}")
		return _FakeEncoding()

	monkeypatch.setattr(tiktoken, "get_encoding", _fake_get_encoding)


# TextSplitter
@pytest.mark.parametrize(
	"chunk_size, chunk_overlap",
	[
		(0, 0),
		(-10, 0),
		(100, -5),
		(100, 100),
		(100, 150),
	],
)
def test_splitter_rejects_invalid_config(chunk_size, chunk_overlap):
	with pytest.raises(InvalidChunkConfigError):
		RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

def test_splitter_rejects_unknown_encoding():
	with pytest.raises(InvalidChunkConfigError):
		RecursiveCharacterTextSplitter(encoding_name="non-existent-encoding")


# RecursiveCharacterTextSplitter
def test_short_document_produces_single_chunk(make_file_metadata):
	document = LoadedDocument(
		document_type="txt",
		content="A short text that fits all in one chunk.",
		metadata=make_file_metadata(),
	)
	splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
	chunks = splitter.split(document)

	assert len(chunks) == 1
	assert chunks[0].content == document.content
	assert chunks[0].chunk_index == 0

def test_empty_document_produces_no_chunks(make_file_metadata):
	document = LoadedDocument(document_type="txt", content="   ", metadata=make_file_metadata())
	splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
	chunks = splitter.split(document)
	assert chunks == []

def test_long_document_is_split_and_no_chunk_exceeds_chunk_size(make_file_metadata):
	paragraph = "This is a test paragraph with several repeated words. " * 4
	content = "\n\n".join([paragraph] * 5)
	document = LoadedDocument(document_type="txt", content=content, metadata=make_file_metadata())
	splitter = RecursiveCharacterTextSplitter(chunk_size=35, chunk_overlap=8)
	chunks = splitter.split(document)

	assert len(chunks) > 1
	assert all(c.token_count <= 35 for c in chunks)
	assert all(c.content.strip() for c in chunks)

def test_chunk_index_is_sequential_without_gaps(make_file_metadata):
	content = "Sentence number one. " * 30
	document = LoadedDocument(document_type="txt", content=content, metadata=make_file_metadata())
	splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=4)
	chunks = splitter.split(document)
	assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

def test_consecutive_chunks_share_overlapping_content(make_file_metadata):
	content = "word. " * 60
	document = LoadedDocument(document_type="txt", content=content, metadata=make_file_metadata())
	splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=10)
	chunks = splitter.split(document)

	assert len(chunks) >= 2
	assert chunks[0].content.strip().endswith("word.")
	assert chunks[1].content.strip().startswith("word.")

def test_chunk_id_is_deterministic_for_same_file_and_index(make_file_metadata):
	content = "Identical text. " * 30
	metadata = make_file_metadata(filepath="/tmp/same_file.txt")
	document = LoadedDocument(document_type="txt", content=content, metadata=metadata)
	splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=4)

	chunks_run_1 = splitter.split(document)
	chunks_run_2 = splitter.split(document)

	assert [c.chunk_id for c in chunks_run_1] == [c.chunk_id for c in chunks_run_2]


# MarkdownAwareTextSplitter
def test_markdown_splitter_assigns_section_title_from_headers(make_file_metadata):
	content = "# Introduction\nShort introductory text.\n\n## Details\nMore short text."
	document = LoadedDocument(document_type="txt", content=content, metadata=make_file_metadata(extension=".md"))
	splitter = MarkdownAwareTextSplitter(chunk_size=100, chunk_overlap=10)
	chunks = splitter.split(document)

	titles = [c.section_title for c in chunks]
	assert "Introduction" in titles[0]
	assert "Details" in titles[-1]
	# Nested breadcrumb child section also includes the parent title
	assert "Introduction" in titles[-1]

def test_markdown_splitter_falls_back_to_recursive_for_oversized_section(make_file_metadata):
	long_section = "## Long section\n" + ("Repeated sentence to exceed chunk size. " * 10)
	document = LoadedDocument(document_type="txt", content=long_section, metadata=make_file_metadata(extension=".md"))
	splitter = MarkdownAwareTextSplitter(chunk_size=15, chunk_overlap=3)
	chunks = splitter.split(document)

	assert len(chunks) > 1
	assert all(c.token_count <= 15 for c in chunks)
	assert all(c.section_title == "Long section" for c in chunks)