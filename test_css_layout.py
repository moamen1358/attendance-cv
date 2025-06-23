#!/usr/bin/env python3
"""
Test the updated CSS and layout changes
"""

import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit/src')

from global_css_handler import apply_global_css

# Set wide layout
st.set_page_config(layout="wide", page_title="CSS Test")

# Apply global CSS
apply_global_css()

st.title("CSS and Layout Test Page")

st.write("This page tests the new CSS implementation:")

st.subheader("Layout Features")
st.write("✅ Wide layout enabled")
st.write("✅ 10px padding from all sides")
st.write("✅ 10px top padding")

# Test with different components
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Test Metric 1", "100%")
    st.info("This is an info box")

with col2:
    st.metric("Test Metric 2", "95%")
    st.success("This is a success box")

with col3:
    st.metric("Test Metric 3", "90%")
    st.warning("This is a warning box")

# Test dataframe
import pandas as pd
df = pd.DataFrame({
    'Column 1': [1, 2, 3, 4, 5],
    'Column 2': ['A', 'B', 'C', 'D', 'E'],
    'Column 3': [10.1, 20.2, 30.3, 40.4, 50.5]
})

st.subheader("Test DataFrame")
st.dataframe(df, use_container_width=True)

# Test plotly chart
import plotly.express as px
fig = px.bar(df, x='Column 2', y='Column 3', title='Test Chart')
st.plotly_chart(fig, use_container_width=True)

st.success("If you can see this page with proper padding and wide layout, the CSS is working correctly!")
