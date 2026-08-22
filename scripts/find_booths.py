import os

import pandas as pd
from dotenv import load_dotenv
from geopy.distance import geodesic
from sqlalchemy import URL, create_engine

load_dotenv()
# Connect to MySQL database and pull the clean data
database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE", "photobooth_project"),
)

engine = create_engine(database_url)
df = pd.read_sql("SELECT Title, URL, latitude, longitude FROM booths WHERE latitude IS NOT NULL", engine)

# Simulate a user's current location (Let's use Manhattan, New York as a test!)
user_latitude = 40.7128
user_longitude = -74.0060
user_location = (user_latitude, user_longitude)

# Define the distance calculation function
def calculate_distance(row):
    booth_location = (row['latitude'], row['longitude'])
    # Computes the distance in miles taking Earth's curvature into account
    return geodesic(user_location, booth_location).miles

# Calculate the distance for every booth and find the top 3 closest
df['distance_miles'] = df.apply(calculate_distance, axis=1)
closest_booths = df.sort_values(by='distance_miles').head(3)

# Print the clean results directly to terminal
print("\n=============================================")
print("🎯 TOP 3 CLOSEST PHOTOBOOTHS TO YOU")
print("=============================================")
for index, row in closest_booths.iterrows():
    print(f"📍 {row['Title']}")
    print(f"   Distance: {row['distance_miles']:.2f} miles away")
    print(f"   Maps Link: {row['URL']}\n")