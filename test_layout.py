import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from professor_subject_assignment import show_professor_assignments

st.set_page_config(page_title="Test Layout", layout="wide")

st.title("Test Professor Assignment Layout")

# Test the professor assignment layout
show_professor_assignments()
