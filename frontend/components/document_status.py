import streamlit as st


def render_document_status(status: str) -> None:
    normalized = status.upper()

    if normalized in {"COMPLETED", "SUCCESS", "PROCESSED"}:
        st.success(f"● {status}")

    elif normalized in {"PROCESSING", "PENDING", "UPLOADED"}:
        st.info(f"● {status}")

    elif normalized in {"FAILED", "ERROR"}:
        st.error(f"● {status}")

    else:
        st.warning(f"● {status}")