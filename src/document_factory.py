from pathlib import Path
from document_loader import (
    DocumentLoader,
    PdfDocumentLoader,
    TxtDocumentLoader,
    DocxDocumentLoader,
    HtmlDocumentLoader
)
from document_exceptions import UnsupportedFormatError

class DocumentLoaderFactory:
  LOADERS_MAP: dict[str, type[DocumentLoader]] = {
    ".pdf": PdfDocumentLoader,
    ".txt": TxtDocumentLoader,
    ".md": TxtDocumentLoader,
    ".docx": DocxDocumentLoader,
    ".html": HtmlDocumentLoader,
    ".htm": HtmlDocumentLoader,
  }
  @classmethod
  def get_loader(cls, file_path: str | Path) -> DocumentLoader:
    path = Path(file_path).resolve()
    if not path.is_file():
      raise FileNotFoundError(f"Unable to find file at path: {path}")
    
    extension = path.suffix.lower()   
    loader_class = cls.LOADERS_MAP.get(extension)
    if not loader_class:
      raise UnsupportedFormatError(
        f"Extension '{extension}' not supported."
      )
    return loader_class(path)