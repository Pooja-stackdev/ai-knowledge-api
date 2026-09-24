from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class LoadedDocument:
    pages: Sequence[DocumentPage]