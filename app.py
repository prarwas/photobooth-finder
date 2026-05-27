import streamlit as st
import pandas as pd
import requests  # Standard library to send HTTP requests over the internet
from streamlit_js_eval import get_geolocation

# Set up the web page title
st.set_page_config(page_title="Photobooth Finder", layout="wide")
st.title("📸 NearMe Photobooth Finder (API-Driven)")
st.write("This app interface fetches its proximity data from a decoupled FastAPI microservice.")

# 1. Sidebar Layout for Location Input
st.sidebar.header("📍 Your Location Settings")

# Trigger the native browser location bridge automatically
location_data = get_geolocation()

user_lat = None
user_lon = None

if location_data and 'coords' in location_data:
    user_lat = location_data['coords']['latitude']
    user_lon = location_data['coords']['longitude']
    st.sidebar.success("🎯 Successfully locked onto your browser location!")
else:
    st.sidebar.info("Waiting for browser location access...")

# Fallback text inputs so the app doesn't crash while waiting for GPS coordinates
st.sidebar.write("---")
st.sidebar.write("Current Coordinates Active:")
manual_lat = st.sidebar.number_input("Latitude", value=user_lat if user_lat else 40.7128, format="%.6f")
manual_lon = st.sidebar.number_input("Longitude", value=user_lon if user_lon else -74.0060, format="%.6f")

# --- NEW DECOUPLED API FETCH LOGIC ---
# Define the URL pointing directly to your local FastAPI server
API_URL = "https://photobooth-api.onrender.com/api/booths"

# Shoot the coordinates across the local network to your API
try:
    response = requests.get(API_URL, params={"lat": manual_lat, "lon": manual_lon})
    
    if response.status_code == 200:
        # Convert the incoming JSON data packet directly back into a clean Pandas DataFrame
        closest_df = pd.DataFrame(response.json())
    else:
        st.error("Failed to fetch data from the API engine.")
        closest_df = pd.DataFrame()
except requests.exceptions.ConnectionError:
    st.error("Could not connect to the API server. Make sure 'uvicorn api:app --reload' is running in your terminal!")
    closest_df = pd.DataFrame()

# 2. Split screen layout: Map on the left, List on the right
if not closest_df.empty:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🗺️ Interactive Proximity Map")
        st.map(closest_df, latitude='latitude', longitude='longitude', size=20)

    with col2:
        st.subheader("🎯 Closest Matches")
        for index, row in closest_df.iterrows():
            st.markdown(f"**📍 {row['Title']}**")
            # The 'distance_miles' calculation comes directly pre-computed by the API!
            st.write(f"Distance: {row['distance_miles']:.2f} miles away")
            st.markdown(f"[View on Google Maps]({row['URL']})")
            st.write("---")