"""
Global styling and dropdown fixes for the entire application
Import this at the top of any page that uses dropdowns
"""
import streamlit as st

def apply_global_dropdown_fixes():
    """Apply comprehensive dropdown and styling fixes"""
    st.markdown("""
    <style>
    /* ===== GLOBAL DROPDOWN FIXES ===== */
    
    /* Force all selectboxes to work properly */
    .stSelectbox {
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    
    .stSelectbox > div[data-baseweb="select"] {
        width: 100% !important;
        min-height: 40px !important;
    }
    
    .stSelectbox > div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        min-height: 38px !important;
        width: 100% !important;
        transition: border-color 0.2s ease !important;
        color: #ffffff !important;
    }
    
    .stSelectbox > div[data-baseweb="select"] > div:hover {
        border-color: #007bff !important;
    }
    
    .stSelectbox > div[data-baseweb="select"] > div:focus-within {
        border-color: #007bff !important;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25) !important;
    }
    
    /* Fix dropdown menu positioning and styling */
    .stSelectbox [role="listbox"] {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        z-index: 9999 !important;
        position: absolute !important;
        width: 100% !important;
        max-height: 300px !important;
        overflow-y: auto !important;
        margin-top: 2px !important;
    }
    
    .stSelectbox [role="option"] {
        padding: 8px 12px !important;
        font-size: 14px !important;
        color: #ffffff !important;
        background-color: #262730 !important;
        border-bottom: 1px solid #404040 !important;
        transition: background-color 0.2s ease !important;
    }
    
    .stSelectbox [role="option"]:hover {
        background-color: #404040 !important;
        color: #ffffff !important;
    }
    
    .stSelectbox [role="option"][aria-selected="true"] {
        background-color: #007bff !important;
        color: #ffffff !important;
    }
    
    /* ===== MULTISELECT FIXES ===== */
    
    .stMultiSelect {
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    
    .stMultiSelect > div[data-baseweb="select"] {
        width: 100% !important;
        min-height: 40px !important;
    }
    
    .stMultiSelect > div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
        border-radius: 6px !important;
        font-size: 14px !important;
        min-height: 38px !important;
        width: 100% !important;
        transition: border-color 0.2s ease !important;
        color: #ffffff !important;
    }
    
    .stMultiSelect > div[data-baseweb="select"] > div:hover {
        border-color: #007bff !important;
    }
    
    .stMultiSelect [role="listbox"] {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        z-index: 9999 !important;
        position: absolute !important;
        width: 100% !important;
        max-height: 300px !important;
        overflow-y: auto !important;
        margin-top: 2px !important;
    }
    
    .stMultiSelect [role="option"] {
        padding: 8px 12px !important;
        font-size: 14px !important;
        color: #ffffff !important;
        background-color: #262730 !important;
        border-bottom: 1px solid #404040 !important;
        transition: background-color 0.2s ease !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background-color: #404040 !important;
        color: #ffffff !important;
    }
    
    .stMultiSelect [role="option"][aria-selected="true"] {
        background-color: #007bff !important;
        color: #ffffff !important;
    }
    
    /* Selected tags in multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #007bff !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        font-size: 12px !important;
        margin: 2px !important;
        padding: 2px 6px !important;
    }
    
    /* ===== FORM STYLING FIXES ===== */
    
    .stForm {
        background-color: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 24px !important;
        margin: 16px 0 !important;
    }
    
    .stButton > button {
        width: 100% !important;
        background-color: #007bff !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        transition: background-color 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* ===== LAYOUT FIXES ===== */
    
    /* Remove excessive spacing */
    .element-container {
        margin-bottom: 8px !important;
    }
    
    /* Fix column alignment */
    .row-widget {
        align-items: flex-start !important;
    }
    
    /* Tab content spacing */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px !important;
    }
    
    /* Ensure containers use full width */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* ===== COLOR CONSISTENCY FIXES ===== */
    
    /* Dark theme for main content area */
    .stApp {
        background-color: #0e1117 !important;
    }
    
    .main {
        background-color: #0e1117 !important;
    }
    
    .main .block-container {
        background-color: #0e1117 !important;
    }
    
    /* Text color consistency for dark theme */
    .stMarkdown, .stText, .stWrite {
        color: #ffffff !important;
    }
    
    /* Header consistency for dark theme */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Form background for dark theme */
    .stForm {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
    }
    
    /* Tab content for dark theme */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #0e1117 !important;
    }
    
    /* Tab headers for dark theme */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #262730 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }
    
    /* ===== RESPONSIVE FIXES ===== */
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .stForm {
            padding: 16px !important;
        }
    }
    
    /* ===== Z-INDEX FIXES ===== */
    
    /* Ensure dropdowns appear above all other elements */
    .stSelectbox [role="listbox"],
    .stMultiSelect [role="listbox"] {
        z-index: 99999 !important;
    }
    
    /* Fix any potential overlay issues */
    .stSidebar {
        z-index: 1000 !important;
    }
    
    .main {
        z-index: 1 !important;
    }
    
    /* ===== ADDITIONAL DARK THEME IMPROVEMENTS ===== */
    
    /* Labels and form labels */
    .stSelectbox label, .stMultiSelect label {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Form input placeholders */
    .stSelectbox input::placeholder, .stMultiSelect input::placeholder {
        color: #cccccc !important;
    }
    
    /* Expander styling for dark theme */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0e1117 !important;
        border: 1px solid #404040 !important;
    }
    
    /* Dataframe styling for dark theme */
    .dataframe {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    .dataframe th {
        background-color: #404040 !important;
        color: #ffffff !important;
    }
    
    .dataframe td {
        background-color: #262730 !important;
        color: #ffffff !important;
    }
    
    /* Alert boxes for dark theme */
    .stAlert {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #155724 !important;
        color: #d4edda !important;
        border: 1px solid #c3e6cb !important;
    }
    
    /* Error message styling */
    .stError {
        background-color: #721c24 !important;
        color: #f8d7da !important;
        border: 1px solid #f5c6cb !important;
    }
    
    /* Warning message styling */
    .stWarning {
        background-color: #856404 !important;
        color: #fff3cd !important;
        border: 1px solid #ffeaa7 !important;
    }
    
    /* Info message styling */
    .stInfo {
        background-color: #0c5460 !important;
        color: #d1ecf1 !important;
        border: 1px solid #bee5eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

def init_page_with_fixes(page_title="Application", layout="wide"):
    """Initialize page with all fixes applied"""
    st.set_page_config(
        page_title=page_title,
        layout=layout,
        initial_sidebar_state="expanded"
    )
    apply_global_dropdown_fixes()

# Auto-apply fixes when this module is imported
apply_global_dropdown_fixes()
