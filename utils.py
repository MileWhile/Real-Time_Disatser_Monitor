# utils.py

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

@st.cache_data(ttl=600)  # Cache the data for 10 minutes (600 seconds)
def load_data():
    """
    Connects to MongoDB using secrets, loads the data, cleans it,
    and returns a pandas DataFrame.
    """
    # Load credentials from secrets
    MONGO_URI = st.secrets["MONGO_URI"]
    DB_NAME = st.secrets["DB_NAME"]
    COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Load data and convert to DataFrame
    df = pd.DataFrame(list(collection.find()))
    
    # --- Start of Centralized Cleaning Logic ---
    df.drop(columns=['_id'], inplace=True, errors='ignore') # Drop mongo's _id
    df.drop_duplicates(subset='title', inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['Latitude', 'Longitude', 'timestamp'], inplace=True)
    
    # Define locations and keywords to exclude
    exclude_locations = ['world', 'global', 'international', 'reuters', 'associated press']
    exclude_keywords_in_url = ['politics', 'yahoo', 'sports', 'entertainment']
    exclude_keywords_in_title = ['tool', 'angry', 'market']
    
    df = df[~df['Location'].str.lower().isin(exclude_locations)]
    df = df[~df['url'].str.lower().str.contains('|'.join(exclude_keywords_in_url))]
    df = df[~df['title'].str.lower().str.contains('|'.join(exclude_keywords_in_title))]

    df['date_only'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df.drop_duplicates(subset=['date_only', 'disaster_event', 'Location'], inplace=True)
    df.drop(columns=['date_only'], inplace=True)
    # --- End of Cleaning Logic ---
    
    print(f"Data loaded and cleaned at {datetime.now()}. Found {len(df)} records.")
    return df