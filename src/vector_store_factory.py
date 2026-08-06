from vector_store import VectorStore, NumpyVectorStore
from vector_store_exceptions import UnsupportedVectorStoreError


class VectorStoreFactory:
    """Registry for VectorStore backends."""

    _registry: dict[str, type[VectorStore]] = {}

    @classmethod
    def register(cls, backend_name: str):
        def decorator(store_cls: type[VectorStore]):
            cls._registry[backend_name] = store_cls
            return store_cls
        return decorator

    @classmethod
    def get_store(cls, backend_name: str, **kwargs) -> VectorStore:
        store_cls = cls._registry.get(backend_name)
        if store_cls is None:
            supported = ", ".join(cls._registry.keys()) or "(no backend registered)"
            raise UnsupportedVectorStoreError(
                f"Backend '{backend_name}' not supported. "
                f"Available backends: {supported}"
            )
        return store_cls(**kwargs)


VectorStoreFactory.register("numpy")(NumpyVectorStore)