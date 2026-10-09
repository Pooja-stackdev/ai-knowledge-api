import streamlit as st

from utils.session import get_current_user


def profile_page() -> None:
    """
    Render the authenticated user's profile.
    """

    user = get_current_user()

    if not user:
        st.error("Unable to load profile.")
        return

    st.title("Profile")
    st.caption("Your account information and effective permissions.")

    st.divider()

    # ---------------------------------------------------------
    # Account information
    # ---------------------------------------------------------

    st.subheader("Account")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Email",
            value=user.get("email", ""),
            disabled=True,
        )

    with col2:
        status = "Active" if user.get("is_active", False) else "Inactive"

        st.text_input(
            "Status",
            value=status,
            disabled=True,
        )

    # ---------------------------------------------------------
    # Roles
    # ---------------------------------------------------------

    st.divider()
    st.subheader("Roles")

    roles = user.get("roles", [])

    if not roles:
        st.info("No roles assigned.")
    else:
        for role in roles:
            st.write(f"• {role['name']}")

    # ---------------------------------------------------------
    # Effective permissions
    # ---------------------------------------------------------

    st.divider()
    st.subheader("Effective Permissions")

    permissions = sorted(user.get("permissions", []))

    if not permissions:
        st.info("No permissions assigned.")
        return

    st.caption(
        "These permissions are calculated from all roles assigned to your account."
    )

    for permission in permissions:
        st.code(permission)