# pages/home.py (Final Version with Map Layers)

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta
from utils import load_data

def main():
    st.title("🌍 Real-Time Disaster Monitor")
    st.markdown("An interactive map showing recent disaster events reported worldwide.")

    with st.spinner('Loading global disaster data, please wait...'):
        df = load_data()

    if df.empty:
        st.info("There is currently no disaster data to display.")
        return

    # --- Sidebar Filters ---
    st.sidebar.header('🗺️ Map Filters')
    
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    default_start_date = max_date - timedelta(days=7)
    
    if default_start_date < min_date:
        default_start_date = min_date
        
    start_date = st.sidebar.date_input("Start date", default_start_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End date", max_date, min_value=start_date, max_value=max_date)

    start_date_utc = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_date_utc = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    unique_events = sorted(df["disaster_event"].unique())
    selected_events = st.multiselect("Filter by Disaster Events", ["All"] + unique_events, default=["All"])

    # Apply filters
    if "All" in selected_events:
        filtered_df = df[(df['timestamp'] >= start_date_utc) & (df['timestamp'] <= end_date_utc)]
    else:
        filtered_df = df[
            (df['timestamp'] >= start_date_utc) & 
            (df['timestamp'] <= end_date_utc) &
            (df['disaster_event'].isin(selected_events))
        ]

    # --- Key Metrics ---
    st.divider()
    total_events = len(filtered_df)
    affected_locations = filtered_df['Location'].nunique()
    col1, col2 = st.columns(2)
    col1.metric("Total Reported Events (in selection)", f"{total_events}")
    col2.metric("Affected Locations (in selection)", f"{affected_locations}")
    st.divider()

    # --- Map Display ---
    if filtered_df.empty:
        st.warning("No disaster data available for the selected filters.")
    else:
        map_center = (filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean())
        mymap = folium.Map(location=map_center, zoom_start=4)
        
        # --- START: NEW Map Layer Code ---
        # Add multiple map styles (Tile Layers) to the map object.
        # The first one added (OpenStreetMap) will be the default.
        folium.TileLayer('OpenStreetMap', name='Street View').add_to(mymap)
        folium.TileLayer('CartoDB Dark_Matter', name='Dark Mode').add_to(mymap)
        folium.TileLayer('Esri.WorldImagery', name='Satellite View').add_to(mymap)
        # --- END: NEW Map Layer Code ---

        marker_cluster = MarkerCluster().add_to(mymap)
        for index, row in filtered_df.iterrows():
            popup_content = f"<b>{row['disaster_event']}</b><br><a href='{row['url']}' target='_blank'>{row['title']}</a>"
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{row['disaster_event']} in {row['Location']}"
            ).add_to(marker_cluster)

        # --- START: Add Layer Control to the Map ---
        # This adds the button that lets the user switch between the layers we defined above.
        folium.LayerControl().add_to(mymap)
        # --- END: Add Layer Control to the Map ---
        
        st_folium(mymap, width='100%', height=500)

if __name__ == "__main__":
    main()