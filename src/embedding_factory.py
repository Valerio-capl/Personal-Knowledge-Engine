from .embedding import EmbeddingProvider, OpenAIEmbeddingProvider
from .embedding_exceptions import UnsupportedEmbeddingProviderError


class EmbeddingProviderFactory:
    """Registry for EmbeddingProvider implementations."""

    _registry: dict[str, type[EmbeddingProvider]] = {}

    @classmethod
    def register(cls, provider_name: str):
        def decorator(provider_cls: type[EmbeddingProvider]):
            cls._registry[provider_name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def get_provider(cls, provider_name: str, **kwargs) -> EmbeddingProvider:
        provider_cls = cls._registry.get(provider_name)
        if provider_cls is None:
            supported = ", ".join(cls._registry.keys()) or "(no provider registered)"
            raise UnsupportedEmbeddingProviderError(
                f"Provider '{provider_name}' not supported. "
                f"Available providers: {supported}"
            )
        return provider_cls(**kwargs)


EmbeddingProviderFactory.register("openai")(OpenAIEmbeddingProvider)