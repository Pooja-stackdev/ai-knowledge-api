from typing import Protocol


class LLMProvider(Protocol):
    """Interface for generating responses from an LLM."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response from the provided prompts."""
        ...