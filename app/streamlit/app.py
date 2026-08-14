import streamlit as st

st.set_page_config(page_title="SafePost AI", page_icon="🛡️")

st.title("🛡️ SafePost AI")
st.caption("Social Media Moderation Console")

text = st.text_area("Enter a social-media post")

if st.button("Analyze Post"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        st.info("Inference UI placeholder — API integration will be implemented in M8.")
