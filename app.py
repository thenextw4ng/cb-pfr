"""CB-PFR Streamlit entrypoint. Route the root URL to the visual research workstation."""
import streamlit as st

st.set_page_config(page_title="CB-PFR · Research Workstation", page_icon="⚛️", layout="wide")
st.switch_page("pages/01_C5G7_Layout_Explorer.py")
