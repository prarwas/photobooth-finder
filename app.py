import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# Set up the web page title
st.set_page_config(page_title="Photobooth Finder", layout="wide")
st.title("📸 NearMe Photobooth Finder")
st.write("This app runs entirely in-memory for instant calculations and 24/7 availability.")

# =====================================================================
# 1. DATA LAYER (LOAD LOCAL CSV DIRECTLY)
# =====================================================================
@st.cache_data
def load_data():
    # Streamlit loads the file directly from your GitHub repo or local folder
    df = pd.read_csv("clean_booths.csv")
    # Clean coordinate types immediately to guarantee rendering safety
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    return df.dropna(subset=['latitude', 'longitude'])

df = load_data()

# =====================================================================
# 2. SIDEBAR LAYOUT & DYNAMIC FILTERS
# =====================================================================
st.sidebar.header("📍 Your Location Settings")

# Dynamically calculate the filter options based on the dataset tags
unique_types = sorted(df['Type'].dropna().unique().tolist())
filter_options = ["All"] + unique_types

booth_filter = st.sidebar.radio(
    "🎞️ Select Photobooth Type:",
    options=filter_options,
    index=0
)
st.sidebar.write("---")

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

# =====================================================================
# 3. IN-MEMORY GEOSPATIAL FILTER ENGINE (REPLACED FASTAPI)
# =====================================================================
user_location = (manual_lat, manual_lon)

# Apply category filtering
if booth_filter != "All":
    filtered_df = df[df['Type'] == booth_filter].copy()
else:
    filtered_df = df.copy()

if not filtered_df.empty:
    # Crunch the geodesic mileage math instantly on the fly
    filtered_df['distance_miles'] = filtered_df.apply(
        lambda row: geodesic(user_location, (row['latitude'], row['longitude'])).miles, 
        axis=1
    )
    
    # Sort and grab the top 5 closest matches
    closest_df = filtered_df.sort_values(by='distance_miles').head(5)
    
    # Map colors cleanly
    def assign_hex_color(row):
        if row.get('Type') == "Vintage":
            return "#FF4B4B"  # Retro Red/Orange
        elif row.get('Type') == "Digital":
            return "#0068C9"  # Clean Tech Blue
        return "#808080"      # Gray fallback
        
    closest_df['pin_color'] = closest_df.apply(assign_hex_color, axis=1)
else:
    closest_df = pd.DataFrame()

# =====================================================================
# 4. SPLIT SCREEN LAYOUT: MAP & BEAUTIFIED CARDS
# =====================================================================
if not closest_df.empty:
    col1, col2 = st.columns([1.8, 1.2])

    with col1:
        st.subheader("🗺️ Interactive Proximity Map")
        st.map(
            closest_df, 
            latitude='latitude', 
            longitude='longitude', 
            size=22,
            color='pin_color'
        )

    with col2:
        st.subheader("🎯 Closest Matches")
        
        for index, row in closest_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### 📍 {row['Title']}")
                
                metric_col1, metric_col2 = st.columns([1, 1])
                with metric_col1:
                    booth_type = row.get('Type', 'Unclassified')
                    if booth_type == "Vintage":
                        st.markdown("🎞️ **Type:** :orange[Vintage]")
                    elif booth_type == "Digital":
                        st.markdown("⚡ **Type:** :blue[Digital]")
                    else:
                        st.markdown(f"📸 **Type:** {booth_type}")
                        
                with metric_col2:
                    st.markdown(f"🏃‍♂️ **Distance:** `{row['distance_miles']:.2f} miles`")
                
                st.write("")
                st.link_button(
                    "🗺️ View on Google Maps", 
                    url=row['URL'], 
                    use_container_width=True
                )
else:
    st.info(f"No {booth_filter} photobooths found matching this area.")