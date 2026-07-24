import os
import requests

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

url = "https://api.upstox.com/v2/instruments/search"

params = {
    "query": "SENSEX",
    "segments": "INDEX",
    "exchanges": "BSE"
}

response = requests.get(url, headers=headers, params=params)

print(response.status_code)
print(response.text)
