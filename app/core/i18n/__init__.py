"""Centralized, request-safe translation helpers."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.core.constants import DEFAULT_LANGUAGE
from app.core.i18n.context import get_current_language

LOCALES_PATH = Path(__file__).parent / "locales"
LANGUAGE_MAP = {
    file.stem: json.loads(file.read_text(encoding="utf-8"))
    for file in LOCALES_PATH.glob("*.json")
}


def _find_message(messages: Mapping[str, Any], key: str) -> str | None:
    value: Any = messages
    
    for part in key.split("."):
        
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value if isinstance(value, str) else None


def get_message(key: str, lang: str | None = None, **params: Any) -> str:
    """Translate a dotted key, falling back safely to English then the key."""
    requested_language = lang or get_current_language()

    message = _find_message(LANGUAGE_MAP.get(requested_language, {}), key)
    
    message = message or _find_message(LANGUAGE_MAP[DEFAULT_LANGUAGE], key)
    
    message = message or key
    try:
        return message.format(**params)
    except (KeyError, ValueError):
        return message


LEGACY_MESSAGE_KEYS = {
    "Unauthorized.": "auth.unauthorized",
    "Authentication required.": "auth.unauthorized",
    "Invalid authentication token.": "auth.invalid_token",
    "Invalid access token.": "auth.invalid_access_token",
    "Token has been revoked.": "auth.token_revoked",
    "Could not validate credentials.": "auth.credentials_invalid",
    "Invalid refresh token": "auth.invalid_refresh_token",
    "User not found": "user.not_found",
    "Document not found": "document.not_found",
    "One or more roles not found": "role.not_found",
    "Permission denied": "auth.forbidden",
    "Role access denied": "auth.forbidden",
    "Request validation failed": "validation.request_failed",
    "An internal database error occurred": "common.database_error",
    "Internal server error": "common.internal_error",
    "Query cannot be empty": "query.empty",
    "You are not authorized to access this document.": "document.forbidden",
    "Document contains no usable chunks": "worker.no_usable_chunks",
    "Embedding count does not match chunk count": "worker.embedding_count_mismatch",
}


def localize_message(message_or_key: str, **params: Any) -> str:
    """Translate a key, including known pre-i18n exception messages."""
    key = LEGACY_MESSAGE_KEYS.get(message_or_key, message_or_key)
    return get_message(key, **params) if "." in key else message_or_key
