import os
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from .base_provider import GenerationProvider
from generation.exceptions import GenerationAPIError, InvalidGenerationConfigError


class OpenAIGenerationProvider(GenerationProvider):
    """Provider based on the OpenAI chat completions API."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str | None = None):
        super().__init__(model_name=model_name)

        resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_api_key:
            raise InvalidGenerationConfigError(
                "OpenAI API key is missing: provide it explicitly with api_key= "
                "or set the OPENAI_API_KEY environment variable"
            )
        self._client = OpenAI(api_key=resolved_api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
        except (RateLimitError, APIConnectionError, APIError) as e:
            raise GenerationAPIError(f"chat.completions.create call failed: {e}") from e

        return response.choices[0].message.content