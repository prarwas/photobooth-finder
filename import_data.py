import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()

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
# 2. LOAD DATA AND EXECUTE EXTRACTION & CLEANING
# =====================================================================
# Load your exact Google Takeout CSV file
csv_file_path = Path(__file__).resolve().parent / "photobooths - photobooths.csv"
df = pd.read_csv(csv_file_path)

print(f"Processing {len(df)} rows from your CSV...")

# Apply the coordinate extraction function across the URL column
df['latitude'], df['longitude'] = zip(*df['URL'].apply(extract_coordinates_from_url))

# --- NEW: EXTRACTION AND CLEANING OF DIGITAL/VINTAGE TAGS ---
# 1. Pull from the 'Tags' column, strip extra whitespace, and capitalize it ('digital' -> 'Digital')
df['Type'] = df['Tags'].str.strip().str.capitalize()

# 2. Correct the spelling typo found in the raw dataset
df['Type'] = df['Type'].replace({'Digial': 'Digital'})
# -------------------------------------------------------------

# Quick console check to verify what it found
found_count = df['latitude'].notna().sum()
print(f"Extraction complete! Successfully parsed coordinates for {found_count}/{len(df)} rows.")

# =====================================================================
# 3. SAVE DATA INTO MYSQL
# =====================================================================
db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")
db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
db_port = int(os.getenv("MYSQL_PORT", "3306"))
db_name = os.getenv("MYSQL_DATABASE", "photobooth_project")

server_url = URL.create(
    "mysql+pymysql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
)

database_url = URL.create(
    "mysql+pymysql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
)

engine = create_engine(server_url)

with engine.connect() as conn:
    conn.execute(
        text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
    )

data_engine = create_engine(database_url)

df.to_sql(
    name="booths",
    con=data_engine,
    if_exists="replace",
    index=False
)

print("Success! Clean photobooth data loaded into MySQL.")