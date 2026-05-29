from fastapi import FastAPI, Query
import pandas as pd
from geopy.distance import geodesic
from typing import Optional

app = FastAPI(title="Photobooth Locator API")

df = pd.read_csv("clean_booths.csv")

# --- NEW ENDPOINT: Dynamically fetch all unique types ---
@app.get("/api/types")
def get_unique_types():
    # Drop empty rows, grab unique values, sort them, and return as a list
    unique_types = df['Type'].dropna().unique().tolist()
    return sorted(unique_types)

@app.get("/api/booths")
def find_nearest_booths(
    lat: float = Query(...), 
    lon: float = Query(...),
    booth_type: Optional[str] = Query(None)
):
    user_location = (lat, lon)
    temp_df = df.copy()
    
    # Dynamically filter by whatever string the frontend sends us!
    if booth_type and booth_type != "All":
        temp_df = temp_df[temp_df['Type'] == booth_type]
        
    if temp_df.empty:
        return []

    def calculate_distance(row):
        return geodesic(user_location, (row['latitude'], row['longitude'])).miles
    
    temp_df['distance_miles'] = temp_df.apply(calculate_distance, axis=1)
    closest = temp_df.sort_values(by='distance_miles').head(5)
    
    return closest.to_dict(orient="records")