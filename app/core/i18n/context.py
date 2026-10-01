"""Request-scoped localization context.

``ContextVar`` values are isolated per request/task, unlike module globals.
Background jobs therefore get the default language unless they explicitly set a
language for a user-facing payload.
"""

from contextvars import ContextVar, Token

from app.core.constants import DEFAULT_LANGUAGE

_current_language: ContextVar[str] = ContextVar(
    "current_language",
    default=DEFAULT_LANGUAGE,
)


def get_current_language() -> str:
    return _current_language.get()


def set_current_language(language: str) -> Token[str]:
    return _current_language.set(language)


def reset_current_language(token: Token[str]) -> None:
    _current_language.reset(token)
