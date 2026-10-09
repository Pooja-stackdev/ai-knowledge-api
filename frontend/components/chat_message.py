import streamlit as st


def render_user_message(content: str) -> None:
    with st.chat_message("user"):
        st.markdown(content)


def render_assistant_message(
    answer: str,
) -> None:
    with st.chat_message("assistant"):
        st.markdown(answer)