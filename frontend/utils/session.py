
from typing import Any

import streamlit as st


def initialize_session() -> None:
    defaults = {
        "access_token": None,
        "refresh_token": None,
        "token_type": "bearer",
        "user": None,
        "authenticated": False,
        "permissions": set(),
        "page": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = (
                value.copy() if isinstance(value, set) else value
            )


def set_authentication(
    access_token: str,
    refresh_token: str,
    token_type: str = "bearer",
) -> None:
    st.session_state["access_token"] = access_token
    st.session_state["refresh_token"] = refresh_token
    st.session_state["token_type"] = token_type
    st.session_state["authenticated"] = True


def _permission_name(permission: Any) -> str | None:
    """Extract a permission name from a string or permission object."""

    if isinstance(permission, str):
        return permission

    if isinstance(permission, dict):
        for key in ("name", "code", "key"):
            value = permission.get(key)
            if isinstance(value, str) and value:
                return value

    return None


def _extract_permissions(user: dict[str, Any]) -> set[str]:
    """Extract direct and role-based permissions from the user response."""

    permissions: set[str] = set()

    def add_permissions(items: Any) -> None:
        if isinstance(items, (list, tuple, set)):
            for item in items:
                name = _permission_name(item)

                if name:
                    permissions.add(name)

                elif isinstance(item, dict):
                    # Support nested permission objects.
                    nested = item.get("permission")
                    if nested is not None:
                        add_permissions(
                            nested if isinstance(nested, (list, tuple, set))
                            else [nested]
                        )

        elif isinstance(items, dict):
            name = _permission_name(items)

            if name:
                permissions.add(name)
            else:
                for value in items.values():
                    if isinstance(value, (list, tuple, set)):
                        add_permissions(value)

    # Direct permissions, if returned by the API.
    add_permissions(user.get("permissions", []))
    add_permissions(user.get("effective_permissions", []))

    # Permissions inherited through roles.
    roles = user.get("roles", [])

    if isinstance(roles, list):
        for role in roles:
            if isinstance(role, dict):
                add_permissions(role.get("permissions", []))

    return permissions


def set_user(user: dict[str, Any]) -> None:
    st.session_state["user"] = user
    st.session_state["permissions"] = _extract_permissions(user)


def set_current_user(user: dict[str, Any]) -> None:
    # Keep backward compatibility with existing callers.
    set_user(user)


def get_current_user() -> dict[str, Any] | None:
    return st.session_state.get("user")


def get_access_token() -> str | None:
    return st.session_state.get("access_token")


def get_refresh_token() -> str | None:
    return st.session_state.get("refresh_token")


def get_permissions() -> set[str]:
    permissions = st.session_state.get("permissions", set())
    return set(permissions)


def has_permission(permission: str) -> bool:
    return permission in get_permissions()


def has_any_permission(*permissions: str) -> bool:
    return bool(get_permissions().intersection(permissions))


def has_all_permissions(*permissions: str) -> bool:
    return get_permissions().issuperset(permissions)


def is_authenticated() -> bool:
    return bool(
        st.session_state.get("authenticated")
        and st.session_state.get("access_token")
    )


def clear_session() -> None:
    for key in (
        "access_token",
        "refresh_token",
        "token_type",
        "user",
        "authenticated",
        "permissions",
        "page",
    ):
        st.session_state.pop(key, None)

    initialize_session()
