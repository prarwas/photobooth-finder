import pandas as pd
from sqlalchemy import create_engine

# Connect to your local MySQL database
engine = create_engine("mysql+pymysql://root:project26@127.0.0.1:3306/photobooth_project")

# Pull the entire table into a DataFrame, now including the clean Type column!
df = pd.read_sql("SELECT Title, URL, latitude, longitude, Type FROM booths WHERE latitude IS NOT NULL", engine)

# Overwrite your deployment file with the fresh dataset
df.to_csv("clean_booths.csv", index=False)

print(f"Success! Exported {len(df)} rows with Digital/Vintage labels into clean_booths.csv")