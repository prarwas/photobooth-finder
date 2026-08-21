import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()

database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE", "photobooth_project"),
)

engine = create_engine(database_url)

df = pd.read_sql(
    """
    SELECT Title, URL, latitude, longitude, Type
    FROM booths
    WHERE latitude IS NOT NULL
      AND longitude IS NOT NULL
    """,
    engine,
)

df.to_csv("clean_booths.csv", index=False)

print(
    f"Success! Exported {len(df)} valid photobooth locations "
    "to clean_booths.csv"
)