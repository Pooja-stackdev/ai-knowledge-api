from langchain_groq import ChatGroq

from app.core.config import settings


class GroqLLMProvider:
    """Generate responses using a Groq-hosted language model."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.llm = ChatGroq(
            api_key=api_key,
            model=model,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            temperature=0,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate a response using system and user prompts."""
        response = self.llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )

        return response.content