class GenerationError(Exception):
    """Base exception for all generation errors."""


class GenerationAPIError(GenerationError):
    """Raised when a provider call fails."""


class InvalidGenerationConfigError(GenerationError):
    """Raised for invalid configuration parameters."""


class UnsupportedGenerationProviderError(GenerationError):
    """Raised when requesting a provider that is not registered in the factory."""