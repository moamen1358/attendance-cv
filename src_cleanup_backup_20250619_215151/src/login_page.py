def show_login_page():
    # Always apply full-width styles at login page load
    from global_css_handler import apply_global_css, enforce_fixed_padding
    apply_global_css()
    enforce_fixed_padding()
    
    # Add JavaScript to ensure fullwidth persists after login
    st.markdown("""
    <script>
        // Store layout preference in localStorage before login
        localStorage.setItem('fullWidthLayout', 'enabled');
        
        // Function to apply full-width layout
        function applyFullWidthLayout() {
            document.querySelectorAll('.block-container, .main .block-container').forEach(el => {
                el.style.maxWidth = '100%';
                el.style.width = '100%';
                el.style.paddingLeft = '40px';
                el.style.paddingRight = '40px';
            });
            
            document.querySelectorAll('[data-testid="stDataFrame"], .js-plotly-plot, .element-container').forEach(el => {
                el.style.maxWidth = '100%';
                el.style.width = '100%';
            });
        }
        
        // Apply immediately and periodically
        applyFullWidthLayout();
        setInterval(applyFullWidthLayout, 1000);
    </script>
    """, unsafe_allow_html=True)

    # When performing logout, completely clear session state
    if 'logout' in st.session_state and st.session_state.logout:
        # Completely reset session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Add JavaScript to ensure full-width layout is reapplied
        st.markdown("""
        <script>
            // Force layout refresh after logout
            sessionStorage.removeItem('fullWidthInitialized');
            localStorage.setItem('fullWidthLayout', 'enabled');
            
            // Force layout to be full width
            document.querySelectorAll('.block-container, .main .block-container').forEach(el => {
                el.style.maxWidth = '100%';
                el.style.width = '100%';
                el.style.paddingLeft = '40px';
                el.style.paddingRight = '40px';
            });
        </script>
        """, unsafe_allow_html=True)
        
        st.query_params.clear()