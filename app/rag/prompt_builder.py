from app.rag.context import RetrievalContext


class PromptBuilder:

    def build(
        self,
        *,
        query: str,
        context: RetrievalContext,
    ) -> tuple[str, str]:
        system_prompt = """
You are a knowledge-base assistant.

Answer the user's question using only the provided context.

Rules:
- Do not use outside knowledge.
- Do not invent information.
- If the answer cannot be found in the context, say that the information
  was not found in the knowledge base.
- Keep the answer concise and factual.
"""

        user_prompt = f"""
Context:

{context.text}

Question:

{query}

Answer the question using only the context above.
"""

        return system_prompt.strip(), user_prompt.strip()