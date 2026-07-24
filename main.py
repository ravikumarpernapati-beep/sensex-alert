import os
import requests

UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
}

url = "https://api.upstox.com/v3/market-quote/quotes?instrument_key=BSE_INDEX|SENSEX"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
