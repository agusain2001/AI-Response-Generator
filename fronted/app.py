# frontend/app.py
import streamlit as st
import requests
import datetime
import os

# --- Configuration ---
# Backend API URL - can be configured via environment variable or hardcoded
# For local development, assuming backend runs on port 8000
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
GENERATE_ENDPOINT = f"{BACKEND_API_URL}/generate"
HISTORY_ENDPOINT = f"{BACKEND_API_URL}/history"

# --- Helper Functions ---
def generate_responses(user_id: str, query: str):
    """Sends request to backend to generate AI responses."""
    payload = {"user_id": user_id, "query": query}
    try:
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=120) # Increased timeout
        response.raise_for_status()  # Raises an exception for HTTP errors (4XX, 5XX)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def get_history(user_id: str):
    """Fetches interaction history for a user from the backend."""
    params = {"user_id": user_id}
    try:
        response = requests.get(HISTORY_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Ensure interactions are present and are a list
        return data.get("interactions", []) if isinstance(data.get("interactions"), list) else []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching history: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching history: {e}")
        return []

# --- Streamlit UI ---
st.set_page_config(page_title="AI Response Generator", layout="wide")

st.title("✨ AI Response Generator ✨")
st.markdown("Get AI-powered responses in different styles!")

# --- User Identification ---
# For demonstration, using a simple text input for user_id.
# In a real app, this would be handled by an authentication system.
if 'user_id' not in st.session_state:
    st.session_state.user_id = "default_user" # Default or prompt

st.sidebar.header("User Settings")
new_user_id = st.sidebar.text_input("Enter User ID:", value=st.session_state.user_id)
if new_user_id != st.session_state.user_id:
    st.session_state.user_id = new_user_id
    st.session_state.history = [] # Clear history if user changes
    st.rerun()

st.sidebar.info(f"Current User ID: **{st.session_state.user_id}**")


# --- Main Interaction Area ---
st.header("📝 Your Query")

with st.form("query_form"):
    user_query = st.text_area("Enter your question or topic:", height=100, key="user_query_input")
    submit_button = st.form_submit_button("🚀 Generate Responses")

if submit_button and user_query:
    if not st.session_state.user_id:
        st.warning("Please enter a User ID in the sidebar.")
    else:
        with st.spinner("🧠 Thinking... Please wait, this might take a moment..."):
            api_response = generate_responses(st.session_state.user_id, user_query)

        if api_response:
            st.session_state.last_response = api_response # Store for display
            # Prepend to history (which will be re-fetched or updated)
            # For now, we'll just rely on re-fetching history to show the latest.
        else:
            st.error("Failed to get responses from the AI. Please check backend logs or try again.")
            st.session_state.last_response = None # Clear previous if error

# Display last responses if available
if 'last_response' in st.session_state and st.session_state.last_response:
    response_data = st.session_state.last_response
    st.subheader(f"🔍 Responses for: \"{response_data.get('query', 'Your Query')}\"")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 😊 Casual Response")
        st.info(response_data.get("casual_response", "No casual response generated."))
    
    with col2:
        st.markdown("### 🧐 Formal Response")
        st.warning(response_data.get("formal_response", "No formal response generated."))
    
    st.markdown(f"<p style='text-align: right; color: grey;'>Generated at: {datetime.datetime.fromisoformat(response_data.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S %Z') if response_data.get('timestamp') else 'N/A'}</p>", unsafe_allow_html=True)
    st.markdown("---")


# --- History Section ---
st.sidebar.header("📜 Interaction History")
if st.sidebar.button("🔄 Refresh History"):
    # Force a refresh by clearing and re-fetching or just re-fetching
    pass # The history will be fetched below anyway

if st.session_state.user_id:
    history_interactions = get_history(st.session_state.user_id)
    if history_interactions:
        st.sidebar.markdown(f"Showing history for **{st.session_state.user_id}**:")
        for i, item in enumerate(history_interactions): # Already sorted newest first by backend
            with st.sidebar.expander(f"{item.get('query', 'Unknown Query')[:30]}... ({datetime.datetime.fromisoformat(item.get('timestamp')).strftime('%Y-%m-%d %H:%M') if item.get('timestamp') else 'N/A'})"):
                st.markdown(f"**Query:** {item.get('query')}")
                st.markdown("**Casual Response:**")
                st.caption(item.get('casual_response'))
                st.markdown("**Formal Response:**")
                st.caption(item.get('formal_response'))
                ts = item.get('timestamp')
                if ts:
                    try:
                        # Ensure timestamp is parsed correctly, handling potential 'Z' for UTC
                        dt_obj = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        st.markdown(f"<small>Timestamp: {dt_obj.strftime('%Y-%m-%d %H:%M:%S %Z')}</small>", unsafe_allow_html=True)
                    except ValueError:
                        st.markdown(f"<small>Timestamp: {ts} (could not parse)</small>", unsafe_allow_html=True)

    else:
        st.sidebar.info("No history found for this user or unable to fetch.")
else:
    st.sidebar.info("Enter a User ID to view history.")

# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>AI Prototype v0.1.0</p>", unsafe_allow_html=True)

