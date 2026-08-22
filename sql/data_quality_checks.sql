SELECT Title, URL, latitude 
FROM booths 
WHERE latitude IS NULL 
LIMIT 5;