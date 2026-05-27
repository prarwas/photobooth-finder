from fastapi import FastAPI, Query
import pandas as pd
from geopy.distance import geodesic

# 1. Initialize the API router
app = FastAPI(
    title="Photobooth Locator API",
    description="Microservice to calculate proximity and find nearby photobooths."
)

# 2. Load our clean dataset into memory once when the server starts
df = pd.read_csv("clean_booths.csv")

# 3. Create a public network endpoint: /api/booths
@app.get("/api/booths")
def find_nearest_booths(lat: float = Query(...), lon: float = Query(...)):
    user_location = (lat, lon)
    
    # 4. Execute the Geodesic Haversine math
    def calculate_distance(row):
        booth_location = (row['latitude'], row['longitude'])
        return geodesic(user_location, booth_location).miles
    
    # Work on a copy of the dataframe so we don't overwrite baseline data
    temp_df = df.copy()
    temp_df['distance_miles'] = temp_df.apply(calculate_distance, axis=1)
    
    # Sort and grab top 5
    closest = temp_df.sort_values(by='distance_miles').head(5)
    
    # 5. Convert the Pandas table into a standardized JSON payload and send it back
    return closest.to_dict(orient="records")