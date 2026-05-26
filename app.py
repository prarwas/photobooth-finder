import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# Import the new browser location tool
from streamlit_js_eval import get_geolocation

# Set up the web page title
st.set_page_config(page_title="Photobooth Finder", layout="wide")
st.title("📸 NearMe Photobooth Finder")
st.write("Find the closest photobooths to any location instantly.")

# 1. Connect to MySQL and pull coordinates
# 1. Read coordinates directly from our local CSV file
@st.cache_data
def load_data():
    # No SQL engine required! This works natively on any computer or cloud server.
    return pd.read_csv("clean_booths.csv")

df = load_data()

# 2. Sidebar Layout for Location Input
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
    st.sidebar.info("Waiting for browser location access... (Ensure permissions are allowed in your browser tab)")

# Fallback text inputs so the map doesn't crash while waiting for GPS coordinates
st.sidebar.write("---")
st.sidebar.write("Current Coordinates Active:")
manual_lat = st.sidebar.number_input("Latitude", value=user_lat if user_lat else 40.7128, format="%.6f")
manual_lon = st.sidebar.number_input("Longitude", value=user_lon if user_lon else -74.0060, format="%.6f")

user_location = (manual_lat, manual_lon)

# 3. Calculate distances on the fly
def calculate_distance(row):
    booth_location = (row['latitude'], row['longitude'])
    return geodesic(user_location, booth_location).miles

df['distance_miles'] = df.apply(calculate_distance, axis=1)
closest_df = df.sort_values(by='distance_miles').head(5)

# 4. Split screen layout: Map on the left, List on the right
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Interactive Proximity Map")
    st.map(closest_df, latitude='latitude', longitude='longitude', size=20)

with col2:
    st.subheader("🎯 Closest Matches")
    for index, row in closest_df.iterrows():
        st.markdown(f"**📍 {row['Title']}**")
        st.write(f"Distance: {row['distance_miles']:.2f} miles away")
        st.markdown(f"[View on Google Maps]({row['URL']})")
        st.write("---")