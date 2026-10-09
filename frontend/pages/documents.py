import streamlit as st

from api.documents import DocumentsAPI
from components.document_status import render_document_status


documents_api = DocumentsAPI()


PROCESSING_STATUSES = {
    "PROCESSING",
    "PENDING",
    "UPLOADED",
}

FAILED_STATUSES = {
    "FAILED",
    "ERROR",
}


def format_datetime(value: str | None) -> str:
    if not value:
        return "-"

    return value.replace("T", " ")[:19]


def has_processing_documents(
    documents: list[dict],
) -> bool:
    return any(
        document.get("status", "").upper()
        in PROCESSING_STATUSES
        for document in documents
    )


def render_document_row(
    document: dict,
    documents_api: DocumentsAPI,
) -> None:
    document_id = document["id"]
    filename = document["filename"]

    status = document.get(
        "status",
        "UNKNOWN",
    ).upper()

    with st.container(border=True):

        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        header_col, status_col = st.columns(
            [4, 1]
        )

        with header_col:
            st.markdown(
                f"### 📄 {filename}"
            )

            st.caption(
                f"Document ID: {document_id}"
            )

        with status_col:
            render_document_status(status)

        # --------------------------------------------------
        # Metadata
        # --------------------------------------------------
        info_col1, info_col2, info_col3 = st.columns(3)

        with info_col1:
            st.caption("Content Type")
            st.write(
                document.get(
                    "content_type",
                    "-",
                )
            )

        with info_col2:
            st.caption("Created")
            st.write(
                format_datetime(
                    document.get("created_at")
                )
            )

        with info_col3:
            st.caption("Updated")
            st.write(
                format_datetime(
                    document.get("updated_at")
                )
            )

        # --------------------------------------------------
        # Description
        # --------------------------------------------------
        description = document.get(
            "description"
        )

        if description:
            st.caption("Description")
            st.write(description)

        # --------------------------------------------------
        # Processing information
        # --------------------------------------------------
        if status in PROCESSING_STATUSES:
            st.info(
                "This document is currently being "
                "processed by the knowledge worker."
            )

        # --------------------------------------------------
        # Processing error
        # --------------------------------------------------
        if status in FAILED_STATUSES:
            last_error = document.get(
                "last_error"
            )

            if last_error:
                with st.expander(
                    "Processing error"
                ):
                    st.error(last_error)
            else:
                st.warning(
                    "Document processing failed. "
                    "You can retry the document."
                )

        # --------------------------------------------------
        # Document details
        # --------------------------------------------------
        with st.expander(
            "Document details"
        ):
            st.write(
                f"**Storage path:** "
                f"`{document.get('storage_path', '-')}`"
            )

            st.write(
                f"**Content type:** "
                f"{document.get('content_type', '-')}"
            )

            st.write(
                f"**Created:** "
                f"{format_datetime(document.get('created_at'))}"
            )

            st.write(
                f"**Updated:** "
                f"{format_datetime(document.get('updated_at'))}"
            )

        # --------------------------------------------------
        # Actions
        # --------------------------------------------------
        action_col1, action_col2, _ = st.columns(
            [1, 1, 4]
        )

        # --------------------------------------------------
        # Retry
        # --------------------------------------------------
        with action_col1:
            if status in FAILED_STATUSES:

                if st.button(
                    "Retry",
                    key=f"retry_{document_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    retry_document(
                        document_id=document_id,
                        documents_api=documents_api,
                    )

        # --------------------------------------------------
        # Delete
        # --------------------------------------------------
        with action_col2:
            if st.button(
                "Delete",
                key=f"delete_{document_id}",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state[
                    "delete_document_id"
                ] = document_id

                st.rerun()

        # --------------------------------------------------
        # Delete confirmation
        # --------------------------------------------------
        if (
            st.session_state.get(
                "delete_document_id"
            )
            == document_id
        ):
            render_delete_confirmation(
                document=document,
                documents_api=documents_api,
            )


def retry_document(
    document_id: int,
    documents_api: DocumentsAPI,
) -> None:
    try:
        with st.spinner(
            "Retrying document..."
        ):
            result = documents_api.retry_document(
                document_id
            )

        new_status = result.get(
            "status",
            "PENDING",
        )

        st.success(
            f"Document queued successfully. "
            f"Status: {new_status}"
        )

        st.rerun()

    except Exception as exc:
        st.error(
            "Unable to retry document."
        )

        st.caption(
            f"Error: {exc}"
        )


def render_delete_confirmation(
    document: dict,
    documents_api: DocumentsAPI,
) -> None:
    document_id = document["id"]
    filename = document["filename"]

    st.warning(
        f"Are you sure you want to delete "
        f"**{filename}**?"
    )

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "Confirm delete",
            key=f"confirm_delete_{document_id}",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "Deleting document..."
                ):
                    documents_api.delete_document(
                        document_id
                    )

                st.session_state.pop(
                    "delete_document_id",
                    None,
                )

                st.success(
                    "Document deleted successfully."
                )

                st.rerun()

            except Exception as exc:
                st.error(
                    "Unable to delete document."
                )

                st.caption(
                    f"Error: {exc}"
                )

    with cancel_col:
        if st.button(
            "Cancel",
            key=f"cancel_delete_{document_id}",
            use_container_width=True,
        ):
            st.session_state.pop(
                "delete_document_id",
                None,
            )

            st.rerun()


def render_upload_section() -> None:
    st.subheader("Upload document")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf"],
        help=(
            "Upload a PDF to the enterprise "
            "knowledge base."
        ),
    )

    description = st.text_area(
        "Description",
        placeholder=(
            "Optional document description"
        ),
        max_chars=1000,
    )

    if uploaded_file is None:
        return

    if st.button(
        "Upload document",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Uploading document..."
            ):
                result = (
                    documents_api.upload_document(
                        file_bytes=(
                            uploaded_file.getvalue()
                        ),
                        filename=uploaded_file.name,
                        content_type=(
                            uploaded_file.type
                            or "application/pdf"
                        ),
                        description=(
                            description.strip()
                            or None
                        ),
                    )
                )

            st.success(
                f"'{result['filename']}' "
                "uploaded successfully."
            )

            st.rerun()

        except Exception as exc:
            st.error(
                "Unable to upload document."
            )

            st.caption(
                f"Error: {exc}"
            )


def render_documents_list(
    documents_api: DocumentsAPI,
) -> None:
    st.subheader("Documents")

    try:
        with st.spinner(
            "Loading documents..."
        ):
            documents = (
                documents_api.list_documents()
            )

    except Exception as exc:
        st.error(
            "Unable to load documents."
        )

        st.caption(
            f"Error: {exc}"
        )

        return

    # ------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------
    refresh_col, count_col = st.columns(
        [1, 5]
    )

    with refresh_col:
        if st.button(
            "↻ Refresh",
            use_container_width=True,
        ):
            st.rerun()

    with count_col:
        st.caption(
            f"{len(documents)} document(s)"
        )

    if not documents:
        st.info(
            "No documents found."
        )

        return

    # ------------------------------------------------------
    # Documents
    # ------------------------------------------------------
    for document in documents:
        render_document_row(
            document=document,
            documents_api=documents_api,
        )

    # ------------------------------------------------------
    # Processing notice
    # ------------------------------------------------------
    if has_processing_documents(
        documents
    ):
        st.info(
            "Some documents are still being "
            "processed by the knowledge worker. "
            "Click Refresh to check the latest status."
        )


def documents_page() -> None:
    st.title("Documents")

    st.caption(
        "Manage documents available to your "
        "authorized knowledge base."
    )

    st.divider()

    render_upload_section()

    st.divider()

    render_documents_list(
        documents_api
    )