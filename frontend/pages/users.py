import streamlit as st
from api.roles import RolesAPI
from api.users import UsersAPI
from constants import SUPER_ADMIN_ROLE_NAME
from utils.session import has_permission


def users_page() -> None:
    """
    Render the Users management page.

    User actions are controlled by effective permissions:
    - user.read   -> access page and list users
    - user.create -> create user
    - user.update -> edit user
    - user.delete -> delete user
    """

    st.title("Users")

    users_api = UsersAPI()

    can_create = has_permission("user.create")
    can_update = has_permission("user.update")
    can_delete = has_permission("user.delete")

    # ---------------------------------------------------------
    # Load users
    # ---------------------------------------------------------

    try:
        users = users_api.list_users()
    except Exception as exc:
        st.error("Unable to load users.")
        st.caption(str(exc))
        return

    # ---------------------------------------------------------
    # Create user
    # ---------------------------------------------------------

    if can_create and st.button(
        "➕ Create User",
        type="primary",
        use_container_width=False,
    ):
        st.session_state["user_action"] = "create"
        st.session_state.pop("edit_user_id", None)

    action = st.session_state.get("user_action")

    if action == "create" and can_create:
        render_create_user_form(users_api)
        return

    # ---------------------------------------------------------
    # Users list
    # ---------------------------------------------------------

    st.divider()

    if not users:
        st.info("No users found.")
        return

    for user in users:
        render_user_row(
            user=user,
            users_api=users_api,
            can_update=can_update,
            can_delete=can_delete,
        )



def render_user_row(
    user: dict,
    users_api: UsersAPI,
    can_update: bool,
    can_delete: bool,
) -> None:
    """Render one user and its available actions."""
    
    user_id = user["id"]
    email = user["email"]
    is_active = user.get("is_active", True)

    # Identify super admin users.
    roles = user.get("role_ids", [])
    
    is_super_admin = 1 in roles
    # is_super_admin = any(
    #     role.get("name", "").lower() == SUPER_ADMIN_ROLE_NAME
    #     for role in roles
    # )
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{email}**")
            st.caption(f"User ID: {user_id}")

        with col2:
            if is_active:
                st.success("Active")
            else:
                st.warning("Inactive")

        with col3:
            if (
                can_update
                and not is_super_admin
                and st.button(
                    "✏️ Edit",
                    key=f"edit_user_{user_id}",
                    use_container_width=True,
                )
            ):
                st.session_state["user_action"] = "edit"
                st.session_state["edit_user_id"] = user_id
                st.rerun()

        with col4:
            if (
                can_delete
                and not is_super_admin
                and st.button(
                    "🗑️ Delete",
                    key=f"delete_user_{user_id}",
                    use_container_width=True,
                )
            ):
                st.session_state["delete_user_id"] = user_id

    if (
        st.session_state.get("delete_user_id") == user_id
        and can_delete
        and not is_super_admin
    ):
        render_delete_confirmation(
            user=user,
            users_api=users_api,
        )

    if (
        st.session_state.get("user_action") == "edit"
        and st.session_state.get("edit_user_id") == user_id
        and can_update
        and not is_super_admin
    ):
        render_edit_user_form(
            user=user,
            users_api=users_api,
        )



def render_create_user_form(users_api: UsersAPI) -> None:
    """
    Render the create-user form.
    """

    st.subheader("Create User")

    roles = get_assignable_roles()

    role_options = {
        role["name"]: role["id"]
        for role in roles
    }

    with st.form("create_user_form"):
        email = st.text_input(
            "Email",
            placeholder="user@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 8 characters",
        )

        selected_roles = st.multiselect(
            "Roles",
            options=list(role_options.keys()),
        )

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button(
                "Create User",
                type="primary",
                use_container_width=True,
            )

        with col2:
            cancelled = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

    if cancelled:
        st.session_state.pop("user_action", None)
        st.rerun()

    if not submitted:
        return

    if not email:
        st.error("Email is required.")
        return

    if not password:
        st.error("Password is required.")
        return

    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    role_ids = [
        role_options[role_name]
        for role_name in selected_roles
    ]

    try:
        users_api.create_user(
            email=email,
            password=password,
            role_ids=role_ids,
        )

        st.success("User created successfully.")

        st.session_state.pop("user_action", None)
        st.rerun()

    except Exception as exc:
        st.error("Unable to create user.")
        st.caption(str(exc))


def render_edit_user_form(
    user: dict,
    users_api: UsersAPI,
) -> None:
    """
    Render the edit-user form.
    """

    st.subheader(f"Edit User: {user['email']}")

    roles = get_assignable_roles()

    role_options = {
        role["name"]: role["id"]
        for role in roles
    }

    # Map assigned role IDs to role names for the multiselect.
    assigned_role_ids = set(user.get("role_ids") or [])

    selected_role_names = [
        role["name"]
        for role in roles
        if role["id"] in assigned_role_ids
    ]

    with st.form(f"edit_user_form_{user['id']}"):
        email = st.text_input(
            "Email",
            value=user["email"],
            disabled=True,
        )

        selected_roles = st.multiselect(
            "Roles",
            options=list(role_options.keys()),
            default=selected_role_names,
        )


        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button(
                "Save Changes",
                type="primary",
                use_container_width=True,
            )

        with col2:
            cancelled = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

    if cancelled:
        st.session_state.pop("user_action", None)
        st.session_state.pop("edit_user_id", None)
        st.rerun()

    if not submitted:
        return

    if not email:
        st.error("Email is required.")
        return

    role_ids = [
        role_options[role_name]
        for role_name in selected_roles
    ]

    try:
        users_api.update_user(
            user_id=user["id"],
            email=email,
            role_ids=role_ids,
        )

        st.success("User updated successfully.")

        st.session_state.pop("user_action", None)
        st.session_state.pop("edit_user_id", None)

        st.rerun()

    except Exception as exc:
        st.error("Unable to update user.")
        st.caption(str(exc))


def render_delete_confirmation(
    user: dict,
    users_api: UsersAPI,
) -> None:
    """
    Render delete confirmation for a user.
    """

    st.warning(
        f"Are you sure you want to delete **{user['email']}**?"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Yes, Delete",
            key=f"confirm_delete_{user['id']}",
            type="primary",
            use_container_width=True,
        ):
            try:
                users_api.delete_user(user["id"])

                st.success("User deleted successfully.")

                st.session_state.pop("delete_user_id", None)
                st.rerun()

            except Exception as exc:
                st.error("Unable to delete user.")
                st.caption(str(exc))

    with col2:
        if st.button(
            "Cancel",
            key=f"cancel_delete_{user['id']}",
            use_container_width=True,
        ):
            st.session_state.pop("delete_user_id", None)
            st.rerun()


def load_roles() -> list[dict]:
    """
    Load roles for user role assignment.
    """

    try:
        return RolesAPI().list_roles()
    except Exception as exc:
        st.error("Unable to load roles.")
        st.caption(str(exc))
        return []


def get_assignable_roles() -> list[dict]:
    """Load roles while excluding the Super Admin role."""
    roles = load_roles()

    return [
        role
        for role in roles
        if role.get("name", "").strip().lower()
        != SUPER_ADMIN_ROLE_NAME.strip().lower()
    ]
