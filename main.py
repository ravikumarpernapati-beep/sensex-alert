import os
import requests

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

instrument_key = "BSE_INDEX|SENSEX"

url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/5minute"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
