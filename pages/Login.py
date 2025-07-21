# pages/login.py (Final Version with Username)

import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials

# --- Credentials Loading ---
try:
    FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]
    firebase_creds_raw = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    firebase_creds_json = json.loads(firebase_creds_raw)
    cred = credentials.Certificate(firebase_creds_json)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    st.error(f"🔥 Firebase/Secrets configuration error: {e}", icon="🔥")
    st.stop()


def main():
    st.title(':green[Welcome to Disaster Monitoring Portal]')

    # Initialize explicit session state variables
    if 'display_name' not in st.session_state: st.session_state.display_name = ''
    if 'user_email' not in st.session_state: st.session_state.user_email = ''
    if 'idToken' not in st.session_state: st.session_state.idToken = ''

    # --- REST API Functions ---
    def handle_login(email, password):
        # ... (This function remains the same as before)
        rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        try:
            r = requests.post(rest_api_url, data=payload)
            r.raise_for_status()
            response_data = r.json()
            st.success("Login Successful!")
            st.session_state.display_name = response_data.get('displayName', response_data.get('email'))
            st.session_state.user_email = response_data.get('email')
            st.session_state.idToken = response_data.get('idToken')
        except requests.exceptions.HTTPError:
            st.error("Login failed. Please check your email and password.")

    def handle_signup(email, password, username):
        # --- THIS FUNCTION IS UPDATED ---
        if not all([email, password, username]):
            st.warning("Please fill out all fields."); return

        # Step 1: Create the user with email and password
        signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
        signup_payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        try:
            r_signup = requests.post(signup_url, data=signup_payload)
            r_signup.raise_for_status()
            signup_data = r_signup.json()
            id_token = signup_data.get('idToken') # Get the token for the newly created user

            if id_token:
                # Step 2: Update the user's profile with the username
                update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_WEB_API_KEY}"
                update_payload = json.dumps({"idToken": id_token, "displayName": username})
                requests.post(update_url, data=update_payload) # We don't need to check the response here

            st.success("Account created successfully! You can now log in.")
            st.balloons()
            
        except requests.exceptions.HTTPError as e:
            error_message = e.response.json().get('error', {}).get('message', "UNKNOWN_ERROR")
            st.error(f"Failed to create account: {error_message}")


    def handle_signout():
        # ... (This function remains the same)
        st.session_state.display_name = ''
        st.session_state.user_email = ''
        st.session_state.idToken = ''

    # --- UI Logic with Username field ---
    if not st.session_state.get('idToken'):
        # Enclose the form in a container with a border
        with st.container(border=True):
            choice = st.selectbox('Select Action', ['Login', 'Sign Up'])

            if choice == 'Login':
                st.subheader("🔐 Login to Your Account")
                email = st.text_input('Email Address')
                password = st.text_input('Password', type='password')
                st.button('Login', on_click=handle_login, args=(email, password), type="primary")
            else: # Signup
                st.subheader("✍️ Create a New Account")
                email = st.text_input("Enter your Email")
                password = st.text_input("Choose a Password", type="password")
                username = st.text_input("Choose a public Username") # <-- NEW USERNAME FIELD
                st.button('Create Account', on_click=handle_signup, args=(email, password, username))
    
    if st.session_state.get('idToken'):
        st.success(f"Welcome, **{st.session_state.display_name}**!")
        st.button('Sign out', on_click=handle_signout)

if __name__ == "__main__":
    main()