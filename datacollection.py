# datacollection.py (Final Corrected Version)

import pandas as pd
import requests
import datetime
import spacy
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from pymongo import MongoClient
import streamlit as st
import time

def main():
    """Main function to run the data collection and storage process."""
    print("--- Starting Data Collection Script ---")
    
    # Load credentials securely
    try:
        NEWSAPI_KEY = st.secrets["NEWSAPI_KEY"]
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
    except KeyError as e:
        print(f"!!! FATAL ERROR: Secret key not found: {e}. Check your .streamlit/secrets.toml file.")
        return

    # Load spaCy model
    try:
        nlp = spacy.load("en_core_web_sm")
        print("spaCy model loaded successfully.")
    except OSError:
        print("!!! FATAL ERROR: spaCy 'en_core_web_sm' model not found. Please run this command:")
        print("python -m spacy download en_core_web_sm")
        return

    geolocator = Nominatim(user_agent="disaster_monitor_geonews_v3")
    NEWSAPI_ENDPOINT = 'https://newsapi.org/v2/everything'
    disaster_keywords = ['earthquake', 'flood', 'tsunami', 'hurricane', 'wildfire', 'forestfire', 'tornado', 'cyclone', 'volcano', 'drought', 'landslide', 'storm', 'blizzard', 'avalanche', 'heatwave']
    
    all_articles = []
    print("\n--- Fetching articles from NewsAPI ---")
    for keyword in disaster_keywords:
        print(f"   > Searching for '{keyword}'...")
        params = {
            'apiKey': NEWSAPI_KEY, 'q': keyword, 'language': 'en', 'pageSize': 30
        }
        try:
            response = requests.get(NEWSAPI_ENDPOINT, params=params)
            response.raise_for_status()
            fetched_articles = response.json().get('articles', [])
            
            # --- THIS IS THE KEY FIX ---
            # Process each article to ensure it has the correct fields
            for article in fetched_articles:
                processed_article = {
                    'title': article.get('title'),
                    'source': article.get('source', {}).get('name'),
                    'url': article.get('url'),
                    'timestamp': article.get('publishedAt'), # Use 'publishedAt' and name it 'timestamp'
                    'disaster_event': keyword.capitalize()
                }
                all_articles.append(processed_article)

        except requests.exceptions.HTTPError as e:
            print(f"     [Error] HTTP Error for '{keyword}': {e.response.status_code}. Check your NewsAPI key.")
        except Exception as e:
            print(f"     [Error] An unexpected error occurred for '{keyword}': {e}")
            
    if not all_articles:
        print("\n!!! SCRIPT STOPPED: No articles were fetched from NewsAPI.")
        return
        
    print(f"\nTotal articles fetched: {len(all_articles)}. Processing...")
    
    df = pd.DataFrame(all_articles)
    df.dropna(subset=['title', 'timestamp', 'url'], inplace=True)
    df.drop_duplicates(subset='title', inplace=True, keep='first')

    print(f"Unique articles after cleaning: {len(df)}. Extracting locations...")
    df['location_ner'] = df['title'].apply(lambda text: [ent.text for ent in nlp(text).ents if ent.label_ == 'GPE'])
    df = df[df['location_ner'].apply(len) > 0]
    df['Location'] = df['location_ner'].apply(lambda x: x[0])
    
    unique_locations = df['Location'].unique()
    print(f"Found {len(unique_locations)} unique locations to geocode...")

    coord_map = {}
    for loc in unique_locations:
        try:
            time.sleep(1) # Add delay to respect geocoding service limits
            location_info = geolocator.geocode(loc, timeout=10)
            if location_info:
                coord_map[loc] = (location_info.latitude, location_info.longitude)
            else:
                coord_map[loc] = (np.nan, np.nan)
        except Exception as e:
            print(f"   [Geocoding Error] for '{loc}': {e}")
            coord_map[loc] = (np.nan, np.nan)
            
    df['Latitude'] = df['Location'].map(lambda loc: coord_map.get(loc, (np.nan, np.nan))[0])
    df['Longitude'] = df['Location'].map(lambda loc: coord_map.get(loc, (np.nan, np.nan))[1])
    df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
    
    final_records = df[['title', 'disaster_event', 'timestamp', 'source', 'url', 'Location', 'Latitude', 'Longitude']].to_dict('records')
    
    if not final_records:
        print("\n!!! SCRIPT STOPPED: No valid records left after processing and geocoding.")
        return

    print(f"\n--- Inserting {len(final_records)} valid records into MongoDB ---")
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Use update_one with upsert=True to avoid duplicates and update existing articles
        for record in final_records:
            collection.update_one(
                {'url': record['url']},  # Find document by its unique URL
                {'$set': record},       # Set its data to the new record
                upsert=True             # If it doesn't exist, create it
            )
        print("\n--- SCRIPT FINISHED SUCCESSFULLY! ---")
        print("Database is now populated. You can run 'streamlit run main.py'.")
        
    except Exception as e:
        print(f"\n!!! FATAL ERROR during MongoDB insertion: {e}")

if __name__ == "__main__":
    main()