import pandas as pd
import re
from sqlalchemy import create_engine, text

# =====================================================================
# 1. CORE COORDINATE EXTRACTION LOGIC
# =====================================================================
def extract_coordinates_from_url(url):
    """
    Parses a Google Maps URL string and extracts latitude and longitude.
    """
    if not url or not isinstance(url, str):
        return None, None
    
    # Format A: Standard coordinate signature (e.g., .../@42.2808,-83.7430...)
    standard_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if standard_match:
        return float(standard_match.group(1)), float(standard_match.group(2))

    # Format B: Encoded business/place signature (e.g., ...!3d42.28082!4d-83.74303...)
    lat_match = re.search(r'!3d(-?\d+\.\d+)', url)
    lng_match = re.search(r'!4d(-?\d+\.\d+)', url)
    if lat_match and lng_match:
        return float(lat_match.group(1)), float(lng_match.group(2))

    return None, None

# =====================================================================
# 2. LOAD DATA AND EXECUTE EXTRACTION
# =====================================================================
# Load your exact Google Takeout CSV file
csv_file_path = "/Users/prxrthxnx/Desktop/photobooth_project/photobooths - photobooths.csv"
df = pd.read_csv(csv_file_path)

print(f"Processing {len(df)} rows from your CSV...")

# Apply the extraction function across the URL column to create the new columns
df['latitude'], df['longitude'] = zip(*df['URL'].apply(extract_coordinates_from_url))

# Quick console check to verify what it found
found_count = df['latitude'].notna().sum()
print(f"Extraction complete! Successfully parsed coordinates for {found_count}/{len(df)} rows.")

# =====================================================================
# 3. SAVE DATA INTO MYSQL
# =====================================================================
# CRITICAL: Replace 'your_password' with your actual MySQL root password!
engine = create_engine("mysql+pymysql://root:project26@127.0.0.1:3306/")

# Ensure the project database exists on your server
with engine.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS photobooth_project;"))

# Connect directly to the photobooth_project database
data_engine = create_engine("mysql+pymysql://root:project26@127.0.0.1:3306/photobooth_project")

# Save the finalized DataFrame into a table named 'booths'
df.to_sql(name="booths", con=data_engine, if_exists="replace", index=False)

print("Success! Upgraded table 'booths' has been successfully loaded into MySQL.")