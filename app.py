import streamlit as st
import pandas as pd
import requests
import pydeck as pdk # Add this line to your imports at the top!
from streamlit_js_eval import get_geolocation

# Set up the web page title
st.set_page_config(page_title="Photobooth Finder", layout="wide")
st.title("📸 NearMe Photobooth Finder (API-Driven)")
st.write("This app interface fetches its proximity data from a decoupled FastAPI microservice.")

# 1. Sidebar Layout for Location Input
st.sidebar.header("📍 Your Location Settings")

# --- NEW: DYNAMIC FILTER FETCH FROM API ---
# Base API URL pointing to your live Render service
BASE_API_URL = "https://photobooth-finder.onrender.com"

try:
    # Ask the API endpoint for all unique categories currently in the database
    types_response = requests.get(f"{BASE_API_URL}/api/types")
    if types_response.status_code == 200:
        # Dynamically build choices: ["All", "Digital", "Vintage", ...]
        filter_options = ["All"] + types_response.json()
    else:
        filter_options = ["All", "Digital", "Vintage"]  # Fallback options
except requests.exceptions.ConnectionError:
    filter_options = ["All", "Digital", "Vintage"]  # Fallback if API is sleeping

# Render the radio buttons on the sidebar using the dynamic list
booth_filter = st.sidebar.radio(
    "🎞️ Select Photobooth Type:",
    options=filter_options,
    index=0
)
st.sidebar.write("---")
# ------------------------------------------

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
st.sidebar.write("Current Coordinates Active:")
manual_lat = st.sidebar.number_input("Latitude", value=user_lat if user_lat else 40.7128, format="%.6f")
manual_lon = st.sidebar.number_input("Longitude", value=user_lon if user_lon else -74.0060, format="%.6f")

# --- DECOUPLED API FETCH LOGIC ---
# Build our payload parameters dynamically
api_params = {"lat": manual_lat, "lon": manual_lon}

# Only send a booth_type filter to the API if the user selected something other than "All"
if booth_filter != "All":
    api_params["booth_type"] = booth_filter

# Shoot the coordinates and filters across the network to your API
try:
    response = requests.get(f"{BASE_API_URL}/api/booths", params=api_params)
    
    if response.status_code == 200:
        # Convert the incoming JSON data packet directly back into a clean Pandas DataFrame
        data_json = response.json()
        if data_json:
            closest_df = pd.DataFrame(data_json)
        else:
            st.info(f"No {booth_filter} photobooths found matching this area.")
            closest_df = pd.DataFrame()
    else:
        st.error("Failed to fetch data from the API engine.")
        closest_df = pd.DataFrame()
except requests.exceptions.ConnectionError:
    st.error("Could not connect to the API server. Make sure your Render web service is awake!")
    closest_df = pd.DataFrame()

# =====================================================================
# 2. SPLIT SCREEN LAYOUT: MAP ON THE LEFT, BEAUTIFIED CARDS ON THE RIGHT
# =====================================================================
if not closest_df.empty:
    col1, col2 = st.columns([1.8, 1.2])  # Slightly wider right column for cards

    with col1:
        st.subheader("🗺️ Interactive Proximity Map")
        
        # 1. Map your text categories to specific RGB color rows [Red, Green, Blue]
        def assign_rgb_color(row):
            if row.get('Type') == "Vintage":
                return [255, 75, 75]   # Retro Red/Orange
            elif row.get('Type') == "Digital":
                return [0, 104, 201]   # Clean Tech Blue
            return [128, 128, 128]     # Gray fallback if unclassified
            
        # Apply the color mapping directly to the data framework
        closest_df['color'] = closest_df.apply(assign_rgb_color, axis=1)

        # 2. Render using high-power Pydeck mapping layers
        # Render using high-power Pydeck mapping layers
        st.pydeck_chart(
            pdk.Deck(
                # CHANGED: Swapped mapbox link for a free, built-in light style
                map_style="carto-positron", 
                initial_view_state=pdk.ViewState(
                    latitude=manual_lat,
                    longitude=manual_lon,
                    zoom=11,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=closest_df,
                        get_position="[longitude, latitude]",
                        get_color="color",
                        get_radius=250, # Radius size of pins in meters
                        pickable=True,
                    ),
                ],
            )
        )

    with col2:
        st.subheader("🎯 Closest Matches")
        
        # Loop through the closest photobooths and render them as clean UI components
        for index, row in closest_df.iterrows():
            # Wrap each booth in its own distinct visual border box
            with st.container(border=True):
                
                # Title Header
                st.markdown(f"### 📍 {row['Title']}")
                
                # Nested row for Type Badge and Distance metrics
                metric_col1, metric_col2 = st.columns([1, 1])
                
                with metric_col1:
                    # Dynamically color-code the badges based on the type
                    booth_type = row.get('Type', 'Unclassified')
                    if booth_type == "Vintage":
                        st.markdown("🎞️ **Type:** :orange[Vintage]")
                    elif booth_type == "Digital":
                        st.markdown("⚡ **Type:** :blue[Digital]")
                    else:
                        st.markdown(f"📸 **Type:** {booth_type}")
                        
                with metric_col2:
                    st.markdown(f"🏃‍♂️ **Distance:** `{row['distance_miles']:.2f} miles`")
                
                # Add a clean space spacing element
                st.write("")
                
                # Native, clickable, full-width button to view directions
                # Giving it a unique key per row prevents Streamlit state errors
                st.link_button(
                    "🗺️ View on Google Maps", 
                    url=row['URL'], 
                    use_container_width=True
                )