import streamlit as st
from api.query import QueryAPI
from components.chat_message import (
    render_assistant_message,
    render_user_message,
)
from components.source_card import render_source_card
from utils.session import (
    get_current_user,
)

query_api = QueryAPI()


def initialize_chat() -> None:
    user = get_current_user()
    user_id = user["id"] if user else None

    if st.session_state.get("chat_user_id") != user_id:
        st.session_state.messages = []
        st.session_state.chat_user_id = user_id

    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat_history() -> None:
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            render_user_message(content)

        elif role == "assistant":
            render_assistant_message(content)

            sources = message.get("sources", [])

            if sources:
                st.markdown("#### Sources")

                for index, source in enumerate(
                    sources,
                    start=1,
                ):
                    render_source_card(
                        source=source,
                        index=index,
                    )


def chat_page() -> None:
    initialize_chat()

    st.title("Knowledge Assistant")

    st.caption(
        "Ask questions about your authorized enterprise documents."
    )

    render_chat_history()

    with st.sidebar:
        st.markdown("### Chat Settings")

        top_k = st.slider(
            "Number of sources",
            min_value=1,
            max_value=20,
            value=5,
            help=(
                "Number of document chunks used "
                "for retrieval."
            ),
        )

        if st.button(
            "Clear conversation",
            use_container_width=True,
        ):
            st.session_state.messages = []
            st.rerun()

    prompt = st.chat_input(
        "Ask a question about your documents..."
    )

    if not prompt:
        return

    prompt = prompt.strip()

    if not prompt:
        return

    render_user_message(prompt)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("assistant"):
        with st.spinner("Searching your knowledge base..."):
            try:
                result = query_api.query(
                    query=prompt,
                    top_k=top_k,
                )

                answer = result.get(
                    "answer",
                    "No answer was returned.",
                )

                sources = result.get(
                    "sources",
                    [],
                )

                st.markdown(answer)

                if sources:
                    st.markdown("#### Sources")

                    for index, source in enumerate(
                        sources,
                        start=1,
                    ):
                        render_source_card(
                            source=source,
                            index=index,
                        )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            except Exception as exc:
                st.error(
                    "Unable to process your question."
                )

                st.caption(
                    f"Error: {exc}"
                )