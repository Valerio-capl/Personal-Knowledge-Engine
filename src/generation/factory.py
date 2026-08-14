from generation.providers import GenerationProvider, OpenAIGenerationProvider, OllamaGenerationProvider
from generation.exceptions import UnsupportedGenerationProviderError


class GenerationProviderFactory:
    """Registry for GenerationProvider implementations."""

    _registry: dict[str, type[GenerationProvider]] = {}

    @classmethod
    def register(cls, provider_name: str):
        def decorator(provider_cls: type[GenerationProvider]):
            cls._registry[provider_name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def get_provider(cls, provider_name: str, **kwargs) -> GenerationProvider:
        provider_cls = cls._registry.get(provider_name)
        if provider_cls is None:
            supported = ", ".join(cls._registry.keys()) or "(no provider registered)"
            raise UnsupportedGenerationProviderError(
                f"Provider '{provider_name}' not supported. "
                f"Available providers: {supported}"
            )
        return provider_cls(**kwargs)


GenerationProviderFactory.register("openai")(OpenAIGenerationProvider)
GenerationProviderFactory.register("ollama")(OllamaGenerationProvider)