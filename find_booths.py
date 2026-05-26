import pandas as pd
from sqlalchemy import create_engine
from geopy.distance import geodesic

# 1. Connect to your MySQL database and pull the clean data you just verified
engine = create_engine("mysql+pymysql://root:project26@127.0.0.1:3306/photobooth_project")
df = pd.read_sql("SELECT Title, URL, latitude, longitude FROM booths WHERE latitude IS NOT NULL", engine)

# 2. Simulate a user's current location (Let's use Manhattan, New York as a test!)
user_latitude = 40.7128
user_longitude = -74.0060
user_location = (user_latitude, user_longitude)

# 3. Define the distance calculation function
def calculate_distance(row):
    booth_location = (row['latitude'], row['longitude'])
    # Computes the distance in miles taking Earth's curvature into account
    return geodesic(user_location, booth_location).miles

# 4. Calculate the distance for every booth and find the top 3 closest
df['distance_miles'] = df.apply(calculate_distance, axis=1)
closest_booths = df.sort_values(by='distance_miles').head(3)

# 5. Print the clean results directly to your terminal
print("\n=============================================")
print("🎯 TOP 3 CLOSEST PHOTOBOOTHS TO YOU")
print("=============================================")
for index, row in closest_booths.iterrows():
    print(f"📍 {row['Title']}")
    print(f"   Distance: {row['distance_miles']:.2f} miles away")
    print(f"   Maps Link: {row['URL']}\n")