import os
import json
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

STATE_FILE = "signal_state.json"

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
# SIGNAL STATE
# ==========================

def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    except:
        return {}


def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ==========================
# MARKET HOURS
# ==========================

def market_open():

    now = datetime.now().time()

    return time(9, 15) <= now <= time(15, 30)


# ==========================
# GET CANDLES
# ==========================

def get_candles(interval=5):
    
    url = (
    "https://api.upstox.com/v3/historical-candle/intraday/"
    f"{INSTRUMENT_KEY}/minutes/{interval}"
)
    
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    
    data = response.json()

    print(response.status_code)
    print(data)

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
    
    # ==========================
# BOLLINGER BANDS
# ==========================

def add_bollinger(df):

    df["ma20"] = df["close"].rolling(20).mean()

    df["std"] = df["close"].rolling(20).std()

    df["upper"] = df["ma20"] + (2 * df["std"])

    df["lower"] = df["ma20"] - (2 * df["std"])

    return df


# ==========================
# SIGNAL LOGIC
# ==========================

def check_signal(df):

    # Minimum candles required
    if len(df) < 21:
        return None

    # Use only CLOSED candles
    prev = df.iloc[-3]
    last = df.iloc[-2]

    # Ignore if Bollinger values are not ready
    if (
        pd.isna(prev["ma20"]) or
        pd.isna(last["ma20"])
    ):
        return None

    # BUY CE
    if (
        prev["close"] <= prev["ma20"] and
        last["close"] > last["ma20"]
    ):
        return {
            "signal": "BUY CE",
            "price": last["close"],
            "time": last["time"],
            "band": last["ma20"]
        }

    # BUY PE
    if (
        prev["close"] >= prev["ma20"] and
        last["close"] < last["ma20"]
    ):
        return {
            "signal": "BUY PE",
            "price": last["close"],
            "time": last["time"],
            "band": last["ma20"]
        }

    return None

# ==========================
# 15M CONFIRMATION
# ==========================

def check_confirmation(df15, pending_signal):

    if len(df15) < 21:
        return None

    last = df15.iloc[-2]

    if pd.isna(last["ma20"]):
        return None

    if pending_signal == "BUY CE":
        return last["close"] > last["ma20"]

    if pending_signal == "BUY PE":
        return last["close"] < last["ma20"]

    return False

# ==========================
# MAIN
# ==========================

def main():

    if not market_open():
        print("Market Closed")
        return
        
    df = get_candles()
    df = add_bollinger(df)
    signal = check_signal(df)

    state = load_state()

    if signal is None:
        print("No Signal")
        return

    current_signal = f"{signal['signal']}_{signal['time']}"

    if state.get("last_signal") == current_signal:
        print("Duplicate Signal")
        return

    state["last_signal"] = current_signal
    state["pending_signal"] = signal["signal"]
    state["pending_time"] = signal["time"]

    save_state(state)
    message = (
        f"📢 SENSEX ALERT\n\n"
        f"Signal : {signal['signal']}\n"
        f"Price  : {signal['price']}\n"
        f"Time   : {signal['time']}\n"
        f"MA20   : {round(signal['band'], 2)}\n\n"
        f"Status : Waiting for 15m Confirmation"
    )

    print(message)

    send_telegram(message)

if __name__ == "__main__":

    try:
        main()

    except Exception as e:

        print(e)

        send_telegram(f"❌ Bot Error\n\n{e}")
