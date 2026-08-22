from pathlib import Path
import streamlit as st
import pandas as pd
import ssl
import certifi
import altair as alt
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

# Set up the web page title
st.set_page_config(page_title="Photobooth Finder", layout="wide")
st.title("📸 NearMe Photobooth Finder")
st.write("Search and compare nearby photobooths using real-time geospatial calculations.")

# =====================================================================
# 1. DATA LAYER (LOAD LOCAL CSV DIRECTLY)
# =====================================================================
DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "processed"
    / "clean_booths.csv"
)

@st.cache_data

def load_data():
    # Streamlit loads the file directly from your GitHub repo or local folder
    df = pd.read_csv(DATA_PATH)
    # Clean coordinate types immediately to guarantee rendering safety
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    return df.dropna(subset=['latitude', 'longitude'])

df = load_data()

# =====================================================================
# 2. SIDEBAR LAYOUT & ADDRESS SELECTION WITH RESET BUTTON
# =====================================================================

st.sidebar.header("📍 Your Location Settings")

unique_types = sorted(df["Type"].dropna().unique().tolist())
filter_options = ["All"] + unique_types

booth_filter = st.sidebar.radio(
    "🎞️ Select Photobooth Style:",
    options=filter_options,
    index=0
)

st.sidebar.write("---")

# Browser geolocation
location_data = get_geolocation()

browser_lat = None
browser_lon = None

if location_data and "coords" in location_data:
    browser_lat = location_data["coords"]["latitude"]
    browser_lon = location_data["coords"]["longitude"]

# Store selected location across Streamlit reruns
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = 40.7282

if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = -73.7949

if "selected_location_name" not in st.session_state:
    st.session_state.selected_location_name = "Queens, New York"


# -------------------------------------------------------------
# Manual location search
# -------------------------------------------------------------

with st.sidebar.form("location_search_form"):

    address_input = st.text_input(
        "Enter an address, neighborhood, or city:",
        placeholder="e.g. Brooklyn, New York"
    )

    search_clicked = st.form_submit_button(
        "🔎 Search Location",
        use_container_width=True
    )


ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)

geolocator = Nominatim(
    user_agent="nearme_photobooth_finder",
    ssl_context=ssl_context
)

if search_clicked:

    if not address_input.strip():

        st.sidebar.warning(
            "Enter a location before searching."
        )

    else:

        try:

            location = geolocator.geocode(
                address_input,
                exactly_one=True
            )

            if location:

                st.session_state.selected_lat = location.latitude
                st.session_state.selected_lon = location.longitude
                st.session_state.selected_location_name = (
                    location.address
                )

                st.sidebar.success(
                    f"Using: {location.address}"
                )

            else:

                st.sidebar.error(
                    "Location not found. Try a more specific address."
                )

        except Exception as exc:

            st.sidebar.error(
                f"Could not resolve that location: {exc}"
            )


# -------------------------------------------------------------
# Browser-location button
# -------------------------------------------------------------

if st.sidebar.button(
    "📍 Use My Current Location",
    use_container_width=True
):

    if browser_lat is not None and browser_lon is not None:

        st.session_state.selected_lat = browser_lat
        st.session_state.selected_lon = browser_lon
        st.session_state.selected_location_name = "Current location"

        st.rerun()

    else:

        st.sidebar.warning(
            "Browser location is not available yet."
        )


manual_lat = st.session_state.selected_lat
manual_lon = st.session_state.selected_lon


st.sidebar.caption(
    f"Current search center: "
    f"{st.session_state.selected_location_name}"
)

st.sidebar.caption(
    f"{manual_lat:.5f}, {manual_lon:.5f}"
)

# =====================================================================
# 3. IN-MEMORY GEOSPATIAL ENGINE (WITH "YOU ARE HERE" PIN)
# =====================================================================
user_location = (manual_lat, manual_lon)

# Apply category filtering first
if booth_filter != "All":
    filtered_df = df[df['Type'] == booth_filter].copy()
else:
    filtered_df = df.copy()

if not filtered_df.empty:
    # 1. Calculate distances for EVERYTHING in the active dataset
    filtered_df['distance_miles'] = filtered_df.apply(
        lambda row: geodesic(user_location, (row['latitude'], row['longitude'])).miles, 
        axis=1
    )
    
    # 2. Sort the entire dataframe so the closest rows are sequentially at the top
    filtered_df = filtered_df.sort_values(by='distance_miles')
    
    # 3. Separate out the absolute Top 5 Closest matches for our side cards
    closest_df = filtered_df.head(5).copy()
    
    # 4. Take the Top 5 CLOSEST + the next 15 spots (20 total locations) for background map space
    map_df = filtered_df.head(20).copy()
    
    # 5. Assign colors (Solid for the top 5 cards, Pastel for the 15 background spots)
    def assign_hex_color(row):
        is_top_5 = row['Title'] in closest_df['Title'].values
        if row.get('Type') == "Vintage":
            return "#FF4B4B" if is_top_5 else "#FFB3B3"
        elif row.get('Type') == "Digital":
            return "#0068C9" if is_top_5 else "#B3D1FF"
        return "#808080" if is_top_5 else "#D3D3D3"
        
    map_df['pin_color'] = map_df.apply(assign_hex_color, axis=1)

    # 6. Create the "YOU ARE HERE" pin right at the resolved address location
    user_pin = pd.DataFrame([{
        'Title': "⭐ YOU ARE HERE",
        'latitude': manual_lat,
        'longitude': manual_lon,
        'Type': "User",
        'pin_color': "#000000",
        'distance_miles': 0.0
    }])
    
    map_df = pd.concat([user_pin, map_df], ignore_index=True)
else:
    closest_df = pd.DataFrame()
    map_df = pd.DataFrame()

# =====================================================================
# 4. SPLIT SCREEN LAYOUT: COMPACT MAP + 5 MATCH CARDS
# =====================================================================
if not closest_df.empty:
    col1, col2 = st.columns([1.8, 1.2])

    with col1:
        st.subheader("🗺️ Interactive Proximity Map")
        st.map(
            map_df, 
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

# =====================================================================
# 5. LOCAL COVERAGE ANALYTICS
# =====================================================================

st.divider()

st.subheader("📊 Local Coverage Insights")

st.caption(
    "Explore photobooth availability around the selected location."
)

if not filtered_df.empty:

    nearest_distance = filtered_df["distance_miles"].min()

    booths_within_1 = int(
        (filtered_df["distance_miles"] <= 1).sum()
    )

    booths_within_5 = int(
        (filtered_df["distance_miles"] <= 5).sum()
    )

    booths_within_10 = int(
        (filtered_df["distance_miles"] <= 10).sum()
    )

    # -------------------------------------------------------------
    # KPI metrics
    # -------------------------------------------------------------

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Nearest Booth",
        f"{nearest_distance:.2f} mi"
    )

    metric2.metric(
        "Within 1 Mile",
        booths_within_1
    )

    metric3.metric(
        "Within 5 Miles",
        booths_within_5
    )

    metric4.metric(
        "Within 10 Miles",
        booths_within_10
    )

    # -------------------------------------------------------------
    # Automatic insight
    # -------------------------------------------------------------

    singular_style_label = (
    "photobooth"
    if booth_filter == "All"
    else f"{booth_filter.lower()} photobooth"
)

    plural_style_label = (
        "photobooths"
        if booth_filter == "All"
        else f"{booth_filter.lower()} photobooths"
    )

    if booths_within_1 > 0:
        insight = (
            f"Strong immediate coverage: {booths_within_1} "
            f"{plural_style_label} are available within 1 mile, "
            f"with {booths_within_5} within 5 miles."
        )

    elif nearest_distance <= 3:
        insight = (
            f"Moderate local coverage: the nearest "
            f"{singular_style_label} is {nearest_distance:.2f} miles away, "
            f"with {booths_within_5} available within 5 miles."
        )

    else:
        insight = (
            f"Limited immediate coverage: the nearest "
            f"{singular_style_label} is {nearest_distance:.2f} miles away. "
            f"There are {booths_within_10} available within 10 miles."
        )

    st.info(insight)

    # -------------------------------------------------------------
    # Distance-band analysis
    # -------------------------------------------------------------

    local_coverage = filtered_df[
        filtered_df["distance_miles"] <= 10
    ].copy()

    if not local_coverage.empty:

        distance_order = [
            "0–1 mi",
            "1–3 mi",
            "3–5 mi",
            "5–10 mi"
        ]

        local_coverage["Distance Band"] = pd.cut(
            local_coverage["distance_miles"],
            bins=[-0.001, 1, 3, 5, 10],
            labels=distance_order
        )

        coverage_counts = (
            local_coverage["Distance Band"]
            .value_counts(sort=False)
            .rename_axis("Distance Band")
            .reset_index(name="Photobooths")
        )

        st.write("#### Availability by Distance")

        distance_chart = (
            alt.Chart(coverage_counts)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Distance Band:N",
                    sort=distance_order,
                    title="Distance from selected location"
                ),
                y=alt.Y(
                    "Photobooths:Q",
                    title="Number of photobooths"
                ),
                tooltip=[
                    alt.Tooltip(
                        "Distance Band:N",
                        title="Distance"
                    ),
                    alt.Tooltip(
                        "Photobooths:Q",
                        title="Photobooths"
                    )
                ]
            )
            .properties(
                height=300
            )
        )

        distance_labels = (
            alt.Chart(coverage_counts)
            .mark_text(
                dy=-10,
                fontSize=14
            )
            .encode(
                x=alt.X(
                    "Distance Band:N",
                    sort=distance_order
                ),
                y="Photobooths:Q",
                text="Photobooths:Q"
            )
        )

        st.altair_chart(
            distance_chart + distance_labels,
            use_container_width=True
        )

    # -------------------------------------------------------------
    # Style distribution
    # -------------------------------------------------------------

    if booth_filter == "All":

        nearby_styles = filtered_df[
            filtered_df["distance_miles"] <= 10
        ]["Type"].fillna("Unclassified")

        if not nearby_styles.empty:

            type_counts = (
                nearby_styles
                .value_counts()
                .rename_axis("Photobooth Style")
                .reset_index(name="Photobooths")
            )

            st.write("#### Styles Available Within 10 Miles")

            style_chart = (
                alt.Chart(type_counts)
                .mark_bar()
                .encode(
                    y=alt.Y(
                        "Photobooth Style:N",
                        sort="-x",
                        title=None
                    ),
                    x=alt.X(
                        "Photobooths:Q",
                        title="Number of photobooths"
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "Photobooth Style:N",
                            title="Style"
                        ),
                        alt.Tooltip(
                            "Photobooths:Q",
                            title="Photobooths"
                        )
                    ]
                )
                .properties(
                    height=250
                )
            )

            st.altair_chart(
                style_chart,
                use_container_width=True
            )

else:

    st.info(
        "Coverage analytics are unavailable because "
        "no photobooths match the current filter."
    )