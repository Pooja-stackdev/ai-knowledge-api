from collections.abc import Sequence
from typing import Protocol


class VectorStore(Protocol):

    def add(
        self,
        ids: Sequence[int],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        ...

    def delete(
        self,
        ids: Sequence[int],
    ) -> None:
        ...

    def search(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        ...