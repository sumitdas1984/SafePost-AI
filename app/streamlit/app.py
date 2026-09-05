"""SafePost AI moderation console — Streamlit UI.

Talks to the FastAPI backend at ``$API_URL`` (default ``http://localhost:8000``).
Set the env var when running under docker compose, ECS, or anywhere the
backend isn't on localhost.
"""
from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="SafePost AI", page_icon="🛡️")

st.title("🛡️ SafePost AI")
st.caption(f"Social Media Moderation Console · backend: `{API_URL}`")

text = st.text_area("Enter a social-media post", height=120)

if st.button("Analyze Post", type="primary"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Classifying..."):
            try:
                response = httpx.post(
                    f"{API_URL}/predict",
                    json={"text": text},
                    timeout=30.0,
                )
                response.raise_for_status()
                body = response.json()
            except httpx.HTTPError as exc:
                st.error(f"Could not reach backend at `{API_URL}`: {exc}")
            except (KeyError, ValueError) as exc:
                st.error(f"Unexpected response from backend: {exc}")
            else:
                label = body["label"]
                confidence = body["confidence"]
                action = body["action"]
                model_version = body.get("model_version", "unknown")

                color_map = {
                    "allow": "#16a34a",
                    "flag": "#d97706",
                    "block": "#dc2626",
                }
                color = color_map.get(action, "#6b7280")

                col1, col2, col3 = st.columns(3)
                col1.metric("Label", label)
                col2.metric("Confidence", f"{confidence:.1%}")
                col3.markdown(
                    f"<div style='background-color:{color};color:white;"
                    f"padding:8px 12px;border-radius:6px;font-weight:600;"
                    f"text-align:center'>{action.upper()}</div>",
                    unsafe_allow_html=True,
                )

                st.caption(f"Model: `{model_version}`")
