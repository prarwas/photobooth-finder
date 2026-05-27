import pandas as pd
from sqlalchemy import create_engine

# Connect to your local MySQL database
engine = create_engine("mysql+pymysql://root:project26@127.0.0.1:3306/photobooth_project")

# Pull the entire table into a DataFrame
df = pd.read_sql("SELECT Title, URL, latitude, longitude FROM booths WHERE latitude IS NOT NULL", engine)

# Save it as actual CSV data, overwriting that old code file
df.to_csv("clean_booths.csv", index=False)

print(f"Success! Exported {len(df)} rows of raw data into clean_booths.csv")