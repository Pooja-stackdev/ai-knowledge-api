import streamlit as st


def has_permission(permission: str) -> bool:
    user = st.session_state.get("user")

    if not user:
        return False

    permissions = user.get("permissions", [])

    return permission in permissions


def has_any_permission(
    permissions: list[str],
) -> bool:
    return any(
        has_permission(permission)
        for permission in permissions
    )


def has_all_permissions(
    permissions: list[str],
) -> bool:
    return all(
        has_permission(permission)
        for permission in permissions
    )