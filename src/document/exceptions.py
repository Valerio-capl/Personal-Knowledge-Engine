class DocumentLoaderError(Exception):
  """Base Exception"""
 
class UnsupportedFormatError(DocumentLoaderError):
  """Raised when the file extension is not supported."""
 
class DocumentParsingError(DocumentLoaderError):
  """Raised when parsing/extraction of a file's contents fails."""
 
class EncodingDetectionError(DocumentLoaderError):
  """Raised when the encoding of a text file cannot be detected or decoded."""
 