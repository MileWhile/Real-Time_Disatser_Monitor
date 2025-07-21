# pages/alerts.py (Final Version with Subscription Status)

import streamlit as st
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pymongo import MongoClient
from datetime import datetime, timezone
from utils import load_data

# --- Helper functions ---

def get_current_subscription(email):
    """Fetches the user's current subscription details from MongoDB."""
    if not email:
        return None
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        SUBSCRIPTIONS_COLLECTION = st.secrets["SUBSCRIPTIONS_COLLECTION"]
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[SUBSCRIPTIONS_COLLECTION]
        return collection.find_one({'email': email})
    except Exception as e:
        st.error(f"Error fetching subscription details: {e}")
        return None

def send_subscription_email(email_receiver):
    # (This function remains unchanged)
    if not email_receiver: return False
    try:
        EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
        EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    except KeyError as e: st.error(f"🔥 Email credentials missing: {e}"); return False

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_SENDER
    msg['To'] = email_receiver
    msg['Subject'] = "Subscription Confirmation"
    html_content = "<html><body><p>Your subscription to Geospatial Disaster Monitoring has been confirmed.</p><p>Best regards,<br>The Team</p></body></html>"
    msg.attach(MIMEText(html_content, 'html'))
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, email_receiver, msg.as_string())
        return True
    except Exception as e: st.error(f"Failed to send confirmation email: {e}"); return False

def save_subscription(email, events, locations):
    # (This function remains unchanged)
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        SUBSCRIPTIONS_COLLECTION = st.secrets["SUBSCRIPTIONS_COLLECTION"]
    except KeyError as e: st.error(f"🔥 DB credentials missing: {e}"); return False
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[SUBSCRIPTIONS_COLLECTION]
        collection.update_one(
            {'email': email},
            {'$set': {"email": email, "selected_events": events, "selected_locations": locations, "subscribed_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        return True
    except Exception as e: st.error(f"Database error: {e}"); return False


# --- Main page function ---
def main():
    st.title("🔔 Subscribe to Custom Alerts")
    
    # Verify user is logged in
    if not st.session_state.get('idToken'):
        st.warning("Please log in to subscribe to alerts.")
        st.info("👈 You can find the Login page in the sidebar.")
        return

    user_email = st.session_state.get('user_email')
    if not user_email:
        st.error("Could not retrieve your email. Please try logging out and in again.")
        return
    
    st.write(f"Configuring alerts for: **{user_email}**")
    st.divider()

    # --- START: New Subscription Status Display ---
    current_sub = get_current_subscription(user_email)
    
    if current_sub:
        with st.container(border=True):
            st.subheader("Your Current Subscription")
            subscribed_events = current_sub.get('selected_events', [])
            subscribed_locations = current_sub.get('selected_locations', [])
            
            if subscribed_events:
                st.write("✅ **Events:**")
                st.write(f"`{', '.join(subscribed_events)}`")
            else:
                st.write("❌ No events subscribed.")
                
            if subscribed_locations:
                st.write("✅ **Locations:**")
                st.write(f"`{', '.join(subscribed_locations)}`")
            else:
                st.write("❌ No locations subscribed.")
    else:
        st.info("You do not have an active alert subscription yet.")
    # --- END: New Subscription Status Display ---
    
    st.divider()

    df = load_data()
    if df.empty: return
    
    st.subheader("Update Your Preferences")
    
    # Set default values for multiselect to match the current subscription
    default_events = current_sub.get('selected_events', []) if current_sub else []
    default_locations = current_sub.get('selected_locations', []) if current_sub else []

    all_events = sorted(df["disaster_event"].unique())
    selected_events = st.multiselect("Select Disaster Events:", options=all_events, default=default_events)

    all_locations = sorted(df["Location"].unique())
    selected_locations = st.multiselect("Select Locations:", options=all_locations, default=default_locations)

    if st.button("Update Subscription", type="primary"):
        if save_subscription(user_email, selected_events, selected_locations):
            if send_subscription_email(user_email):
                st.success("Subscription updated successfully! A confirmation email has been sent.")
                st.balloons()
            else:
                st.warning("Your subscription was saved, but the confirmation email could not be sent.")
            # Rerun to instantly show the updated subscription status
            st.rerun()

if __name__ == "__main__":
    main()