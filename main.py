import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, time

# ==========================
# CONFIG
# ==========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

INSTRUMENT_KEY = "BSE_INDEX|SENSEX"

URL = (
    "https://api.upstox.com/v3/historical-candle/intraday/"
    f"{INSTRUMENT_KEY}/minutes/5"
)

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
}


# ==========================
# TELEGRAM
# ==========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=20
    )


# ==========================
# MARKET HOURS
# ==========================

def market_open():

    now = datetime.now().time()

    return time(9, 15) <= now <= time(15, 30)


# ==========================
# GET CANDLES
# ==========================

def get_candles():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    data = response.json()

    candles = data["data"]["candles"]

    df = pd.DataFrame(
        candles,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "oi"
        ]
    )

    df = df.iloc[::-1].reset_index(drop=True)

    df["close"] = df["close"].astype(float)

    return df
