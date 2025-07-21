# pages/insight.py (Final Version with Improved Layout)

import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from datetime import timedelta
from utils import load_data

def main():
    # --- Page Title and Introduction ---
    st.title("📊 Insights & Analytics Dashboard")
    st.markdown("Explore trends and distributions in the global disaster data.")

    # --- Data Loading with Spinner ---
    with st.spinner('Analyzing data, please wait...'):
        df = load_data()

    if df.empty:
        st.info("There is currently no data available to generate insights.")
        return
        
    df['date'] = df['timestamp'].dt.date

    # --- Sidebar Filters for Analytics ---
    st.sidebar.header('📈 Analytics Filters')
    min_date = df['date'].min()
    max_date = df['date'].max()

    default_start_date = max_date - timedelta(days=30)
    if default_start_date < min_date:
        default_start_date = min_date

    start_date = st.sidebar.date_input(
        "Start date for Insights", default_start_date, min_value=min_date, max_value=max_date, key="insight_start"
    )
    end_date = st.sidebar.date_input(
        "End date for Insights", max_date, min_value=start_date, max_value=max_date, key="insight_end"
    )
    
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    if filtered_df.empty:
        st.warning("No data found in the selected date range.")
        return

    # --- START: New Chart Layout using Columns ---
    st.divider()
    col1, col2 = st.columns(2, gap="large") # Use a large gap for better spacing

    with col1:
        st.subheader("Top 10 Affected Locations")
        location_counts = filtered_df['Location'].value_counts().nlargest(10)
        
        fig_loc = px.bar(
            location_counts,
            y=location_counts.index,
            x=location_counts.values,
            orientation='h',
            labels={'y': 'Location', 'x': 'Number of Reports'},
            text_auto=True # Display the count on each bar
        )
        # Sort the bars so the largest is at the top
        fig_loc.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        st.plotly_chart(fig_loc, use_container_width=True)
    
    with col2:
        st.subheader("Disaster Event Proportions")
        event_counts = filtered_df['disaster_event'].value_counts()
        
        fig_event = px.pie(
            event_counts,
            names=event_counts.index,
            values=event_counts.values,
            hole=0.4, # Creates a "donut" chart
            title="Event Breakdown"
        )
        fig_event.update_layout(height=400, showlegend=False)
        fig_event.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_event, use_container_width=True)

    st.divider()

    st.subheader("Disaster Reports Over Time")
    # Group data by day and count the number of events
    time_counts = filtered_df.set_index('timestamp').resample('D').size().reset_index(name='count')
    
    fig_time = px.area(
        time_counts, 
        x='timestamp', 
        y='count',
        labels={'timestamp': 'Date', 'count': 'Daily Event Count'},
        title="Daily Volume of Disaster Reports"
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.divider()
    # --- END: New Chart Layout ---
    
    st.subheader("Common Terms in Disaster Headlines")
    text_data = ' '.join(title for title in filtered_df['title'].dropna())
    
    if text_data:
        wordcloud = WordCloud(
            width=800, height=300, background_color='white', collocations=False
        ).generate(text_data)
        st.image(wordcloud.to_array(), use_container_width=True)

if __name__ == "__main__":
    main()