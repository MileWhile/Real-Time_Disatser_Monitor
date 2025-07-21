# notification_engine.py

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import streamlit as st # We use this ONLY to access secrets
import json

# --- Helper Functions ---

def send_alert_email(recipient_email, disaster):
    """Formats and sends a single disaster alert email."""
    try:
        EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
        EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    except KeyError as e:
        print(f"Error: Email credentials missing from secrets.toml: {e}")
        return False

    disaster_title = disaster.get('title', 'N/A')
    disaster_url = disaster.get('url', '#')
    disaster_event = disaster.get('disaster_event', 'N/A')
    disaster_location = disaster.get('Location', 'N/A')
    
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient_email
    msg['Subject'] = f"New Disaster Alert: {disaster_event} in {disaster_location}"
    
    html_content = f"""
    <html><body>
    <h3>Disaster Alert</h3>
    <p>A new potential disaster event has been detected that matches your subscription criteria.</p>
    <ul>
      <li><strong>Event Type:</strong> {disaster_event}</li>
      <li><strong>Location:</strong> {disaster_location}</li>
    </ul>
    <p><strong>Headline:</strong> {disaster_title}</p>
    <p><a href="{disaster_url}" target="_blank">Click here to read the full article.</a></p>
    <br>
    <p><small>You are receiving this because you subscribed to alerts on the Global Disaster Monitor.</small></p>
    </body></html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        print(f"   -> Successfully sent alert to {recipient_email}")
        return True
    except Exception as e:
        print(f"   -> FAILED to send email to {recipient_email}: {e}")
        return False

def check_for_alerts():
    """The main engine function. Finds new disasters and emails matching subscribers."""
    print(f"\n--- Running Alert Check at {datetime.now(timezone.utc).isoformat()} ---")

    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        DISASTER_COLLECTION = st.secrets["COLLECTION_NAME"]
        SUBS_COLLECTION = st.secrets["SUBSCRIPTIONS_COLLECTION"]
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        disaster_collection = db[DISASTER_COLLECTION]
        subs_collection = db[SUBS_COLLECTION]
    except KeyError as e:
        print(f"Error: MongoDB credentials missing from secrets.toml: {e}")
        return

    # To find "new" disasters, we fetch disasters from the last 30 minutes.
    # A more robust system would use a flag like `alert_sent: true`.
    time_window = datetime.now(timezone.utc) - timedelta(minutes=30)
    new_disasters = list(disaster_collection.find({"timestamp": {"$gte": time_window}}))

    if not new_disasters:
        print("No new disasters found in the last 30 minutes. Ending check.")
        return
        
    print(f"Found {len(new_disasters)} recent disaster reports to process.")

    all_subscriptions = list(subs_collection.find())
    if not all_subscriptions:
        print("No user subscriptions found. Ending check.")
        return
        
    # --- The Core Matching Logic ---
    alerts_sent_count = 0
    for disaster in new_disasters:
        event = disaster["disaster_event"]
        location = disaster["Location"]
        print(f"\nProcessing: {event} in {location}")
        
        # Find all users subscribed to this specific event AND location
        matching_subscribers = [
            sub for sub in all_subscriptions
            if event in sub.get("selected_events", []) and location in sub.get("selected_locations", [])
        ]
        
        if matching_subscribers:
            print(f"  Found {len(matching_subscribers)} matching subscriber(s).")
            for subscriber in matching_subscribers:
                if send_alert_email(subscriber["email"], disaster):
                    alerts_sent_count += 1
        else:
            print("  No matching subscribers found for this event.")
            
    print(f"\n--- Alert Check Finished. Sent {alerts_sent_count} total alert(s). ---")


if __name__ == "__main__":
    check_for_alerts()