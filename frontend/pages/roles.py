import streamlit as st
from api.permissions import PermissionsAPI
from api.roles import RolesAPI
from constants import SUPER_ADMIN_ROLE_NAME
from utils.session import has_permission


def roles_page() -> None:
    """
    Render the Roles management page.

    Role actions are controlled by effective permissions.
    The permissions catalog is loaded only when the user
    has role creation or update permission.
    """
    st.title("Roles")

    roles_api = RolesAPI()

    can_create = has_permission("role.create")
    # can_update = has_permission("role.update")
    can_delete = has_permission("role.delete")

    permissions = []

    if can_create:
        permissions_api = PermissionsAPI()
        permissions = permissions_api.list_permissions()

    roles = [
        role
        for role in roles_api.list_roles()
        if role.get("name", "").strip().lower()
        != SUPER_ADMIN_ROLE_NAME.strip().lower()
    ]

    if can_create and st.button("➕ Create Role"):
        st.session_state["role_action"] = "create"

    action = st.session_state.get("role_action")

    if action == "delete" and can_delete:
        role_id = st.session_state["selected_role_id"]

        role = next(
            (
                role
                for role in roles
                if role["id"] == role_id
            ),
            None,
        )

        if role:
            st.warning(
                f"Delete role '{role['name']}'?"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Confirm Delete",
                    type="primary",
                ):
                    roles_api.delete_role(role_id)

                    st.session_state.pop(
                        "role_action",
                        None,
                    )
                    st.session_state.pop(
                        "selected_role_id",
                        None,
                    )

                    st.rerun()

            with col2:
                if st.button("Cancel"):
                    st.session_state.pop(
                        "role_action",
                        None,
                    )
                    st.session_state.pop(
                        "selected_role_id",
                        None,
                    )
                    st.rerun()

        return

    if action == "edit":
        role_id = st.session_state["selected_role_id"]

        role = roles_api.get_role(role_id)

        render_role_form(
            roles_api=roles_api,
            permissions=permissions,
            role=role,
        )

        return

    if action == "create" and can_create:
        render_role_form(
            roles_api=roles_api,
            permissions=permissions,
        )
        return

    st.divider()

    for role in roles:
        render_role_row(
            role=role,
            roles_api=roles_api,
            permissions=permissions,
            can_update=False,
            can_delete=can_delete,
        )


def render_role_row(
    role: dict,
    roles_api: RolesAPI,
    permissions: list[dict],
    can_update: bool,
    can_delete: bool,
) -> None:
    """
    Render a single role and its available actions.
    """
    col1, col2 = st.columns([5, 1])

    with col1:
        st.write(role["name"])

    # with col2:
    #     if can_update and st.button(
    #         "Edit",
    #         key=f"edit_role_{role['id']}",
    #     ):
    #         st.session_state["role_action"] = "edit"
    #         st.session_state["selected_role_id"] = role["id"]
    #         st.rerun()

    with col2:
        if can_delete and st.button(
            "Delete",
            key=f"delete_role_{role['id']}",
        ):
            st.session_state["role_action"] = "delete"
            st.session_state["selected_role_id"] = role["id"]
            st.rerun()


def render_role_form(
    roles_api: RolesAPI,
    permissions: list[dict],
    role: dict | None = None,
) -> None:
    """
    Render the create or update role form.
    """
    is_edit = role is not None

    st.subheader(
        "Edit Role" if is_edit else "Create Role"
    )

    name = st.text_input(
        "Role name",
        value=role["name"] if role else "",
    )

    permission_options = {
        permission["name"]: permission["id"]
        for permission in permissions
    }

    current_permissions = []

    if role:
        current_permissions = [
            permission["name"]
            for permission in role.get("permissions", [])
        ]

    selected_permissions = st.multiselect(
        "Permissions",
        options=list(permission_options.keys()),
        default=current_permissions,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save",
            type="primary",
        ):
            if not name.strip():
                st.error("Role name is required.")
                return

            permission_ids = [
                permission_options[name]
                for name in selected_permissions
            ]

            payload = {
                "name": name.strip(),
                "permission_ids": permission_ids,
            }

            if is_edit:
                roles_api.update_role(
                    role["id"],
                    payload,
                )
            else:
                roles_api.create_role(payload)

            st.session_state.pop("role_action", None)
            st.session_state.pop("selected_role_id", None)

            st.success("Role saved successfully.")
            st.rerun()

    with col2:
        if st.button("Cancel"):
            st.session_state.pop("role_action", None)
            st.session_state.pop("selected_role_id", None)
            st.rerun()