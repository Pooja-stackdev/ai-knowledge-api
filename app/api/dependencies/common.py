
from typing import Annotated

from fastapi import Depends, Header

SUPPORTED_LANGUAGES = {"en", "gu", "hi"}


def get_language_from_header(accept_language: str | None) -> str:
    """Return the supported primary language tag, defaulting to English."""
    if not accept_language:
        return "en"

    language = accept_language.split(",", maxsplit=1)[0].split("-", maxsplit=1)[0].lower()

    if language not in {"en", "gu", "hi"}:
        return "en"

    return language


def get_language(
    accept_language: Annotated[str | None, Header()] = None,
) -> str:
    return get_language_from_header(accept_language)


CurrentLanguage = Annotated[str, Depends(get_language)]
