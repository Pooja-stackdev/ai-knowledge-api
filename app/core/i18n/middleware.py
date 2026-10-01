"""Middleware that establishes the localization context for each request."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.api.dependencies.common import get_language_from_header
from app.core.i18n.context import reset_current_language, set_current_language


async def localization_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Resolve ``Accept-Language`` once and reset it when the request ends."""
    language = get_language_from_header(request.headers.get("accept-language"))
    request.state.language = language
    token = set_current_language(language)
    try:
        return await call_next(request)
    finally:
        reset_current_language(token)
