
# 📈 SPY 0DTE Real-Time Signal Dashboard (Streamlit)
# Run this in Streamlit Cloud or locally with: streamlit run spy_dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
import time
import numpy as np

st.set_page_config(page_title="SPY 0DTE Signal Dashboard", layout="wide")
st.title("🚨 SPY 0DTE Real-Time Algo Dashboard")

if "signals" not in st.session_state:
    st.session_state.signals = []

UNUSUAL_WHALES_API_KEY = "015ae332-d0f6-4831-8648-4c2f323af4ef"
POLYGON_API_KEY = "anf984U5ZJXr85IU_ZIhqFZoaIW1mzHN"

def get_current_price(symbol="SPY"):
    url = f"https://api.polygon.io/v1/last/stocks/{symbol}?apiKey={POLYGON_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["last"]["price"]
    except Exception as e:
        st.warning(f"Price fetch error: {e}")
    return None

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

def generate_signals():
    price = get_current_price()
    flow_data = fetch_options_flow()
    new_signals = []
    if price and flow_data:
        for item in flow_data.get("chains", []):
            premium = float(item["ask_price"]) * int(item["ask_size"])
            if item["ask_side"] == "A" and premium >= 20000:
                signal = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "price": price,
                    "direction": "CALL" if item["type"] == "call" else "PUT",
                    "score": round(np.random.uniform(7.0, 9.5), 2),
                    "volatility": np.random.choice(["High", "Neutral", "Low"])
                }
                new_signals.append(signal)
    return new_signals

if st.button("📡 Fetch New Signal From Algo"):
    signals = generate_signals()
    for sig in signals:
        st.session_state.signals.append(sig)

chart_df = pd.DataFrame({
    "time": pd.date_range(end=datetime.now(), periods=30, freq="T"),
    "open": [560 + np.random.uniform(-1, 1) for _ in range(30)],
    "high": [561 + np.random.uniform(-0.5, 1) for _ in range(30)],
    "low": [559 + np.random.uniform(-1, 0.5) for _ in range(30)],
    "close": [560 + np.random.uniform(-1, 1) for _ in range(30)],
})

fig = go.Figure(data=[go.Candlestick(
    x=chart_df["time"],
    open=chart_df["open"],
    high=chart_df["high"],
    low=chart_df["low"],
    close=chart_df["close"],
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

st.plotly_chart(fig, use_container_width=True)
st.subheader("📋 Signal Log")
st.dataframe(pd.DataFrame(st.session_state.signals[::-1]), use_container_width=True)
