import streamlit as st


def render_source_card(
    source: dict,
    index: int,
) -> None:
    document_id = source.get("document_id")
    page_number = source.get("page_number")
    content = source.get("content", "")

    with st.expander(
        f"Source {index} · Document #{document_id} · Page {page_number}"
    ):
        st.caption(
            f"Document ID: {document_id}  |  "
            f"Chunk ID: {source.get('chunk_id')}"
        )

        st.markdown(content)