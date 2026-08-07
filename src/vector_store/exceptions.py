class VectorStoreError(Exception):
    """Base exception for all vector store errors."""

class VectorDimensionMismatchError(VectorStoreError):
    """Raised when a vector (during insertion or query) has a
    different dimension than the one configured for the store."""

class EmbeddingModelMismatchError(VectorStoreError):
    """Raised when attempting to insert chunks generated with an
    embedding model different from the one already present in the store."""

class VectorStorePersistenceError(VectorStoreError):
    """Raised when saving or loading the store from disk fails."""

class InvalidVectorStoreConfigError(VectorStoreError):
    """Raised for invalid configuration parameters."""

class UnsupportedVectorStoreError(VectorStoreError):
    """Raised when requesting a backend that is not registered in the factory."""