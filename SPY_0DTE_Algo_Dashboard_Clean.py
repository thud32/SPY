# 📈 SPY 0DTE Real-Time Signal Dashboard (Streamlit)
# Run this with: streamlit run spy_dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import numpy as np
import time

# ------------------------------------
# Streamlit Page Setup
# ------------------------------------
st.set_page_config(page_title="SPY 0DTE Signal Dashboard", layout="wide")
st.title("🚨 SPY 0DTE Real-Time Algo Dashboard")

# Session state to store signal log
if "signals" not in st.session_state:
    st.session_state.signals = []

# ------------------------------------
# API Config
# ------------------------------------
UNUSUAL_WHALES_API_KEY = "015ae332-d0f6-4831-8648-4c2f323af4ef"
POLYGON_API_KEY = "anf984U5ZJXr85IU_ZIhqFZoaIW1mzHN"

# ------------------------------------
# Price & Chart Utility (Polygon.io)
# ------------------------------------
def get_intraday_candles(symbol="SPY"):
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(minutes=30)
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{from_date.date()}?adjusted=true&sort=asc&limit=1000&apiKey={POLYGON_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("results", [])
            df = pd.DataFrame(data)
            df["t"] = pd.to_datetime(df["t"], unit="ms")
            return df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close"})
    except Exception as e:
        st.warning(f"Chart fetch error: {e}")
    return pd.DataFrame()

# ------------------------------------
# Flow Utility (Unusual Whales)
# ------------------------------------
def fetch_options_flow():
    url = "https://api.unusualwhales.com/api/historic_chains"
    headers = {"Authorization": f"Bearer {UNUSUAL_WHALES_API_KEY}"}
    params = {
        "ticker": "SPY",
        "limit": 50,
        "min_premium": 20000,
        "order_by": "ask_size",
        "sort": "desc",
        "type": "call,put"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"Flow fetch error: {e}")
    return None

# ------------------------------------
# Signal Trigger Logic
# ------------------------------------
def generate_signals(current_price):
    flow_data = fetch_options_flow()
    new_signals = []
    if current_price and flow_data:
        for item in flow_data.get("chains", []):
            premium = float(item["ask_price"]) * int(item["ask_size"])
            if item["ask_side"] == "A" and premium >= 20000:
                signal = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "price": current_price,
                    "direction": "CALL" if item["type"] == "call" else "PUT",
                    "score": round(np.random.uniform(7.0, 9.5), 2),
                    "volatility": np.random.choice(["High", "Neutral", "Low"])
                }
                new_signals.append(signal)
    return new_signals

# ------------------------------------
# Main Loop
# ------------------------------------
placeholder_chart = st.empty()
placeholder_log = st.empty()

while True:
    candle_data = get_intraday_candles()
    if candle_data.empty:
        st.warning("Unable to load chart data.")
        break

    current_price = candle_data["close"].iloc[-1]
    signals = generate_signals(current_price)
    for sig in signals:
        st.session_state.signals.append(sig)

    fig = go.Figure(data=[go.Candlestick(
        x=candle_data["t"],
        open=candle_data["open"],
        high=candle_data["high"],
        low=candle_data["low"],
        close=candle_data["close"],
        name="SPY"
    )])

    for signal in st.session_state.signals:
        fig.add_trace(go.Scatter(
            x=[datetime.now()],
            y=[signal["price"]],
            mode="markers+text",
            marker=dict(color="green" if signal["direction"] == "CALL" else "red", size=12),
            text=["CALL" if signal["direction"] == "CALL" else "PUT"],
            textposition="top center",
            name=f"{signal['direction']} @ {signal['time']}"
        ))

    fig.update_layout(
        title="Live SPY Chart with Algo Triggers",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600
    )

    placeholder_chart.plotly_chart(fig, use_container_width=True)
    placeholder_log.dataframe(pd.DataFrame(st.session_state.signals[::-1]), use_container_width=True)
    time.sleep(15)
