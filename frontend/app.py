import streamlit as st
from api.auth import AuthAPI
from pages.chat import chat_page
from pages.documents import documents_page
from pages.roles import roles_page
from pages.users import users_page
from pages.profile import profile_page
from utils.session import (
    clear_session,
    get_current_user,
    has_permission,
    initialize_session,
    is_authenticated,
    set_authentication,
    set_user,
    get_permissions
)

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Enterprise RAG",
    page_icon="🤖",
    layout="wide",
)


# ---------------------------------------------------------
# Session initialization
# ---------------------------------------------------------

initialize_session()

auth_api = AuthAPI()


# ---------------------------------------------------------
# Page styles
# ---------------------------------------------------------

# def apply_page_styles() -> None:
#     """
#     Apply global Streamlit page styles.

#     Hides the sidebar and sidebar toggle when the user
#     is not authenticated.
#     """
#     if not is_authenticated():
#         st.markdown(
#             """
#             <style>
#                 /* Hide sidebar */
#                 [data-testid="stSidebarNav"] {
#                     display: none !important;
#                 }

#                 [data-testid="stSidebar"] {
#                     display: none !important;
#                 }

#                 /* Hide sidebar expand/collapse button */
#                 [data-testid="stSidebarCollapsedControl"] {
#                     display: none !important;
#                 }

#             </style>
#             """,
#             unsafe_allow_html=True,
#         )

def apply_page_styles() -> None:
    """
    Hide Streamlit's default multipage navigation
    without hiding the custom sidebar.
    """
    st.markdown(
        """
        <style>
            /* Hide only the default Streamlit page menu */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not is_authenticated():
        st.markdown(
            """
            <style>
                /* Hide sidebar */
                [data-testid="stSidebar"] {
                    display: none !important;
                }

                /* Hide sidebar expand/collapse button */
                [data-testid="stSidebarCollapsedControl"] {
                    display: none !important;
                }

            </style>
            """,
            unsafe_allow_html=True,
        )


# Apply styles before rendering the page.
apply_page_styles()


# ---------------------------------------------------------
# Login page
# ---------------------------------------------------------

def login_page() -> None:
    """
    Render the login page and authenticate the user.

    On successful authentication:
    - Stores access and refresh tokens.
    - Fetches the current user from /auth/me.
    - Stores the authenticated user in the session.
    - Reloads the application.
    """
    st.title("Enterprise RAG")

    st.caption(
        "Secure enterprise knowledge assistant"
    )

    st.divider()

    with st.form("login_form"):
        st.subheader("Sign in")

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
            type="primary",
        )

    if not submitted:
        return

    if not email or not password:
        st.error(
            "Email and password are required."
        )
        return

    try:
        with st.spinner("Signing in..."):
            token_data = auth_api.login(
                email=email,
                password=password,
            )

            set_authentication(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "bearer"),
            )

            user = auth_api.get_me()
            set_user(user)

            # Reset stale navigation from a previous session.
            st.session_state["page"] = get_default_page()

        # Exit the login form and rerun the app.
        st.rerun()


    except Exception as exc:
        st.error("Unable to sign in.")
        st.caption(str(exc))


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------


def render_sidebar() -> None:
    user = get_current_user()
    permissions = get_permissions()

    with st.sidebar:
        st.title("Enterprise RAG")
        st.divider()

        if user:
            st.caption("Signed in as")
            st.write(user.get("email", "Unknown user"))

        st.divider()
        st.markdown("### Navigation")

        menu_items = [
            ("chat", "💬 Chat", "query.execute"),
            ("documents", "📄 Documents", "document.read"),
            ("users", "👥 Users", "user.read"),
            ("roles", "🔐 Roles", "role.read"),
        ]

        for page_key, label, permission in menu_items:
            if permission not in permissions:
                continue

            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type=(
                    "primary"
                    if st.session_state.get("page") == page_key
                    else "secondary"
                ),
            ):
                st.session_state["page"] = page_key
                st.rerun()

        st.divider()

        if st.button("👤 Profile", key="nav_profile", use_container_width=True):
            st.session_state["page"] = "profile"
            st.rerun()

        if st.button("Logout", key="logout", use_container_width=True):
            try:
                auth_api.logout()
            except Exception:
                pass

            clear_session()
            st.rerun()


# ---------------------------------------------------------
# Default page
# ---------------------------------------------------------

def get_default_page() -> str:
    """
    Determine the first page available to the user.

    Pages are selected based on effective permissions.
    """
    if has_permission("query.execute"):
        return "chat"

    if has_permission("document.read"):
        return "documents"

    if has_permission("user.read"):
        return "users"

    if has_permission("role.read"):
        return "roles"

    return "profile"


# ---------------------------------------------------------
# Page routing
# ---------------------------------------------------------

def render_page(page: str) -> None:
    """
    Render the requested application page.

    Page access is checked again before rendering so that
    navigation visibility is not the only protection.
    """
    if page == "chat":
        if not has_permission("query.execute"):
            st.error(
                "You do not have permission to access Chat."
            )
            return

        chat_page()
        return

    if page == "documents":
        if not has_permission("document.read"):
            st.error(
                "You do not have permission to access Documents."
            )
            return

        documents_page()
        return

    if page == "users":
        if not has_permission("user.read"):
            st.error(
                "You do not have permission to access Users."
            )
            return

        users_page()
        return

    if page == "roles":
        if not has_permission("role.read"):
            st.error(
                "You do not have permission to access Roles."
            )
            return

        roles_page()
        return

    if page == "profile":
        profile_page()
        return

    st.error("Invalid page.")


# ---------------------------------------------------------
# Authenticated application
# ---------------------------------------------------------

def authenticated_app() -> None:
    """
    Render the authenticated application.

    Initializes the default page, renders the sidebar,
    and routes the user to the selected page.
    """

    if "page" not in st.session_state:
        st.session_state["page"] = get_default_page()

    render_sidebar()

    page = st.session_state["page"]
    render_page(page)


# ---------------------------------------------------------
# Application entry point
# ---------------------------------------------------------

def main() -> None:
    """
    Run the Streamlit application.

    Displays the login page for unauthenticated users
    and the authenticated application for logged-in users.
    """
    initialize_session()

    if is_authenticated():
        authenticated_app()
    else:
        login_page()


if __name__ == "__main__":
    main()