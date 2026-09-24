from langchain_groq import ChatGroq


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