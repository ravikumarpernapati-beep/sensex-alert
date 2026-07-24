import os
import requests

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

instrument_key = "BSE_INDEX|SENSEX"

url = f"https://api.upstox.com/v3/historical-candle/intraday/{instrument_key}/minutes/5"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
