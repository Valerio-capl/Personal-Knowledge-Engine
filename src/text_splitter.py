import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
import tiktoken
from document_loader import LoadedDocument, FileMetadata
from document_exceptions import DocumentLoaderError

class InvalidChunkConfigError(DocumentLoaderError):
  """Raised when chunking parameters are invalid."""
 
 
@dataclass(frozen=True)
class Chunk:
    content: str
    chunk_index: int
    token_count: int
    source_metadata: FileMetadata
    chunk_id: str
    section_title: str | None = None
    
    
class TextSplitter(ABC):
    """Base class for splitters.."""
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, encoding_name: str = "cl100k_base"):
        if chunk_size <= 0:
            raise InvalidChunkConfigError("chunk_size must be a positive integer")
        if chunk_overlap < 0:
            raise InvalidChunkConfigError("chunk_overlap can't be negative")
        if chunk_overlap >= chunk_size:
            raise InvalidChunkConfigError("chunk_overlap must be strictly smaller than chunk_size")
    
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:
            self._encoding = tiktoken.get_encoding(encoding_name)
        except ValueError as e:
            raise InvalidChunkConfigError(f"Invalid encoding: {encoding_name}") from e
    
    @abstractmethod
    def split(self, document: LoadedDocument) -> list[Chunk]:
        """ splitt LoadedDocument in chunk list """
        pass
    
    def _count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text, disallowed_special=()))
    
    @staticmethod
    def _make_chunk_id(filepath: str, chunk_index: int) -> str:
        raw = f"{filepath}:{chunk_index}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class RecursiveCharacterTextSplitter(TextSplitter):
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size = 500, chunk_overlap = 50, encoding_name = "cl100k_base",separators: list[str] | None = None):
        super().__init__(chunk_size, chunk_overlap, encoding_name)
        self.separators = separators or self.DEFAULT_SEPARATORS

    def split(self, document: LoadedDocument) -> list[Chunk]:
        raw_pieces = self._split_text(document.content, self.separators)
        chunks = self._build_chunks(raw_pieces, document.metadata)
        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        if not text.strip():
            return []
    
        if self._count_tokens(text) <= self.chunk_size: #base case 
            return [text]
    
        separator = separators[0]
        remaining_separators = separators[1:]
        splits = list(text) if separator == "" else text.split(separator)
        good_splits: list[str] = []
        final_pieces: list[str] = []
    
        for i, split in enumerate(splits):
            is_last = i == len(splits) - 1
            piece = split if (separator == "" or is_last) else split + separator
        
            if self._count_tokens(piece) <= self.chunk_size:
                good_splits.append(piece)
                continue
        
            if good_splits:
                final_pieces.extend(self._merge_splits(good_splits))
                good_splits = []
        
            if remaining_separators:
                final_pieces.extend(self._split_text(piece, remaining_separators)) # if piece>chunk_size 
            else:
                final_pieces.append(piece)
    
        if good_splits:
            final_pieces.extend(self._merge_splits(good_splits))
    
        return final_pieces
    
    def _merge_splits(self, splits: list[str]) -> list[str]:
        merged: list[str] = []
        current: list[str] = []
        current_tokens = 0
    
        for piece in splits:
            piece_tokens = self._count_tokens(piece)
            if current and current_tokens + piece_tokens > self.chunk_size:
                merged.append("".join(current))
                current, current_tokens = self._build_overlap(current)
            current.append(piece)
            current_tokens += piece_tokens
    
        if current:
            merged.append("".join(current)) 
    
        return merged

    def _build_overlap(self, previous_pieces: list[str]) -> tuple[list[str], int]:
        """Builds the overlap for the next chunk, taking the last pieces of the previous chunk until it reaches the chunk_overlap token."""
        overlap_pieces: list[str] = []
        overlap_tokens = 0
    
        for piece in reversed(previous_pieces):
            piece_tokens = self._count_tokens(piece)
            if overlap_tokens + piece_tokens > self.chunk_overlap:
                break
            overlap_pieces.insert(0, piece)
            overlap_tokens += piece_tokens
    
        return overlap_pieces, overlap_tokens
    
    def _build_chunks(self, raw_pieces: list[str], metadata: FileMetadata) -> list[Chunk]:
        chunks = []
        idx = 0
        for text in raw_pieces:
            text = text.strip()
            if not text:
                continue
            chunks.append(Chunk(
                content=text,
                chunk_index=idx,
                token_count=self._count_tokens(text),
                source_metadata=metadata,
                chunk_id=self._make_chunk_id(metadata.filepath, idx),
            ))
            idx += 1
        return chunks
    
class MarkdownAwareTextSplitter(TextSplitter):
    """Splitter for markdown"""
 
    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, encoding_name: str = "cl100k_base",):
        super().__init__(chunk_size, chunk_overlap, encoding_name)
        self._fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size, chunk_overlap, encoding_name
        )
 
    def split(self, document: LoadedDocument) -> list[Chunk]:
        sections = self._split_by_headers(document.content)
        chunks: list[Chunk] = []
        idx = 0
    
        for section_title, section_text in sections:
            if self._count_tokens(section_text) <= self.chunk_size:
                chunks.append(Chunk(
                    content=section_text,
                    chunk_index=idx,
                    token_count=self._count_tokens(section_text),
                    source_metadata=document.metadata,
                    chunk_id=self._make_chunk_id(document.metadata.filepath, idx),
                    section_title=section_title,
                ))
                idx += 1
                continue

            sub_pieces = self._fallback_splitter._split_text(section_text, self._fallback_splitter.separators)
            for sub_text in sub_pieces:
                sub_text = sub_text.strip()
                if not sub_text:
                    continue
                chunks.append(Chunk(
                    content=sub_text,
                    chunk_index=idx,
                    token_count=self._count_tokens(sub_text),
                    source_metadata=document.metadata,
                    chunk_id=self._make_chunk_id(document.metadata.filepath, idx),
                    section_title=section_title,
                ))
                idx += 1

        return chunks
 
    def _split_by_headers(self, text: str) -> list[tuple[str | None, str]]:
        lines = text.split("\n")
        sections: list[tuple[str | None, str]] = []
        title_stack: list[tuple[int, str]] = []
        current_lines: list[str] = []
    
        def flush():
            content = "\n".join(current_lines).strip()
            if content:
                title = " > ".join(t for _, t in title_stack) if title_stack else None
                sections.append((title, content))
                
        for line in lines:
            match = self.HEADER_PATTERN.match(line)
            if match:
                flush()
                current_lines = [line]
                level = len(match.group(1))
                title = match.group(2).strip()
                title_stack = [t for t in title_stack if t[0] < level]
                title_stack.append((level, title))
            else:
                current_lines.append(line)
            
        flush()
        return sections
