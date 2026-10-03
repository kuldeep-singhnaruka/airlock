import os

import httpx
import streamlit as st

st.set_page_config(page_title="Airlock", layout="wide")
st.title("Airlock")
st.caption("Streamlit client for the Airlock inference service.")

if "token" not in st.session_state:
    st.session_state.token = ""
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    base_url = st.text_input("API base URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    username = st.text_input("Username", os.getenv("DEMO_USERNAME", "demo"))
    password = st.text_input("Password", os.getenv("DEMO_PASSWORD", "demo-pass"), type="password")
    if st.button("Login"):
        try:
            response = httpx.post(
                f"{base_url}/v1/auth/token",
                json={"username": username, "password": password},
                timeout=30,
            )
        except httpx.HTTPError as exc:
            st.error(f"API unreachable: {exc}")
        else:
            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.success("Authenticated")
            else:
                st.error(response.text)
    enable_tools = st.checkbox("Enable tools", value=True)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state.token}"}


chat_tab, extract_tab, usage_tab = st.tabs(["Chat", "Structured extract", "Usage"])

with chat_tab:
    for item in st.session_state.history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    prompt = st.chat_input("Ask the model")
    if prompt:
        if not st.session_state.token:
            st.warning("Login first.")
        else:
            st.session_state.history.append({"role": "user", "content": prompt})
            try:
                response = httpx.post(
                    f"{base_url}/v1/chat",
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "enable_tools": enable_tools,
                    },
                    headers=_headers(),
                    timeout=60,
                )
            except httpx.HTTPError as exc:
                st.error(f"API unreachable: {exc}")
            else:
                if response.status_code != 200:
                    st.error(response.text)
                else:
                    body = response.json()
                    answer = body["content"]
                    if body["tool_trace"]:
                        lines = "\n".join(
                            f"- `{trace['name']}`: {trace['result']}"
                            for trace in body["tool_trace"]
                        )
                        answer = f"{answer}\n\nTool trace:\n{lines}"
                    st.session_state.history.append({"role": "assistant", "content": answer})
                    st.rerun()

with extract_tab:
    schema_name = st.selectbox("Schema", ["task", "sentiment"])
    text = st.text_area("Text", "Please fix the login bug today, this is urgent")
    if st.button("Extract"):
        if not st.session_state.token:
            st.warning("Login first.")
        else:
            response = httpx.post(
                f"{base_url}/v1/extract",
                json={"text": text, "schema_name": schema_name},
                headers=_headers(),
                timeout=60,
            )
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error(response.text)

with usage_tab:
    if st.button("Refresh usage"):
        if not st.session_state.token:
            st.warning("Login first.")
        else:
            response = httpx.get(f"{base_url}/v1/usage", headers=_headers(), timeout=30)
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error(response.text)
