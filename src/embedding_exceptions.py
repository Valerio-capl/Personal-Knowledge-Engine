class EmbeddingError(Exception):
    """Base exception for all embedding errors"""


class EmbeddingAPIError(EmbeddingError):
    """Raised when a provider call fails after all retry attempts have been exhausted."""


class EmbeddingDimensionMismatchError(EmbeddingError):
    """Raised when the vector returned by a provider has a different
    dimension than the one declared or expected for the model."""


class InvalidEmbeddingConfigError(EmbeddingError):
    """Raised when the configuration is invalid"""


class UnsupportedEmbeddingProviderError(EmbeddingError):
    """Raised when requesting a provider that is not registered."""