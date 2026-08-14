from abc import ABC, abstractmethod

class GenerationProvider(ABC):
    """Base interface for text generation providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Sends the prompt to the underlying model and returns its text response."""
        pass