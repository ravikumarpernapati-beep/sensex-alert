import os
import json
import requests
import pandas as pd
from datetime import datetime, time

# ==========================
# CONFIG
# ==========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

INSTRUMENT_KEY = "BSE_INDEX|SENSEX"

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
        return {
            "last_signal": "",
            "pending_signal": "",
            "pending_time": ""
        }

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    except:
        return {
            "last_signal": "",
            "pending_signal": "",
            "pending_time": ""
        }


def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


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
# BOLLINGER
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

    if len(df) < 21:
        return None

    prev = df.iloc[-3]
    last = df.iloc[-2]

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

    # 5-Minute Data
    df = get_candles()
    df = add_bollinger(df)
    signal = check_signal(df)

    state = load_state()

    # --------------------------
    # Check Pending 15M Signal
    # --------------------------
    if state.get("pending_signal"):

        df15 = get_candles(15)
        df15 = add_bollinger(df15)

        confirmed = check_confirmation(
            df15,
            state["pending_signal"]
        )

        if confirmed is True:

            send_telegram(
                f"✅ 15M CONFIRMED\n\n{state['pending_signal']}"
            )

            state["pending_signal"] = ""
            state["pending_time"] = ""

            save_state(state)

        elif confirmed is False:

            send_telegram(
                f"❌ 15M REJECTED\n\n{state['pending_signal']}"
            )

            state["pending_signal"] = ""
            state["pending_time"] = ""

            save_state(state)

    # --------------------------
    # No New Signal
    # --------------------------
    if signal is None:
        print("No Signal")
        return

    current_signal = f"{signal['signal']}_{signal['time']}"

    # --------------------------
    # Duplicate Check
    # --------------------------
    if state.get("last_signal") == current_signal:
        print("Duplicate Signal")
        return

    # Save New Signal
    state["last_signal"] = current_signal
    state["pending_signal"] = signal["signal"]
    state["pending_time"] = signal["time"]

    save_state(state)

    # Telegram Alert
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


# ==========================
# START
# ==========================

if __name__ == "__main__":

    try:
        main()

    except Exception as e:

        print(e)

        send_telegram(
            f"❌ Bot Error\n\n{e}"
        )
