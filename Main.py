# main.py (New Simplified Version)

import streamlit as st

# Set page configuration
# This is the only place you need to set this, and it will apply to all pages
st.set_page_config(
    page_title="Real-Time Disaster Monitor",
    page_icon="🌍",
    layout="wide"
)

# Main welcome page content
st.title("🌍 Welcome to the Real-Time Disaster Monitor")
st.sidebar.success("Select a page above to begin.")

st.markdown(
    """
    This application is designed to provide real-time monitoring and visualization
    of disaster events around the world. By analyzing news articles and other open
    sources, we provide actionable insights for disaster response agencies and the public.
    
    ### How to use this application:
    - **Home**: View an interactive map of recent global disaster events.
    - **Insight**: Explore analytics and trends about disaster occurrences.
    - **Alerts**: Log in and subscribe to custom alerts for specific events and locations.
    - **Precaution**: Read safety protocols for various disaster types.
    - **About**: Learn more about the project, its data sources, and technologies used.
    
    **👈 Select a page from the sidebar to get started!**
    """
)