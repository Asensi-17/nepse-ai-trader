from flask import Flask, jsonify
import pandas as pd
import requests, time, threading
from collections import defaultdict
from threading import Lock
from io import StringIO

from core.indicators import add_indicators
from core.patterns import detect_order_blocks, detect_fvg, detect_liquidity, detect_pd_zones
from core.strategy import compute_score, get_trade_levels, update_weights

from core.database import insert_trade, insert_signal
from core.sector import compute_sector_strength, sector_map

from core.mtf import resample_tf, get_trend
from core.liquidity import liquidity_heatmap
from core.accumulation import detect_accumulation

from core.regime import detect_regime
from core.adaptive import adjust_parameters

app = Flask(__name__)

# =============================
# GLOBALS
# =============================
tick_buffer = defaultdict(list)
candles_1m = defaultdict(list)

open_positions = {}
last_trade_time = {}
last_alert_time = {}

equity = 100000
equity_curve = [equity]

lock = Lock()

CANDLE = 60
MAX_POSITIONS = 4
COOLDOWN = 1200

# =============================
# TELEGRAM
# =============================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except Exception as e:
        print("Telegram Error:", e)

# =============================
# MARKET TIME FILTER
# =============================
def is_market_active():
    h = time.localtime().tm_hour
    return 11 <= h <= 15

# =============================
# FETCH
# =============================
def fetch_data():
    try:
        url = "https://www.sharesansar.com/live-trading"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()

        tables = pd.read_html(StringIO(r.text))
        if not tables:
            return pd.DataFrame()

        df = tables[0]

        # validation
        required_cols = ['Symbol', 'LTP', 'Volume']
        if not all(col in df.columns for col in required_cols):
            print("⚠️ TABLE STRUCTURE CHANGED")
            return pd.DataFrame()

        df = df.rename(columns={
            'Symbol': 'Stock',
            'LTP': 'Close',
            'Volume': 'Volume'
        })

        df = df[['Stock', 'Close', 'Volume']]

        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')

        df = df.dropna()

        print("✅ SHARESANSAR DATA OK")
        return df

    except Exception as e:
        print("FETCH ERROR:", e)
        return pd.DataFrame()

# =============================
# TICKS
# =============================
def update_ticks(df):
    now = int(time.time())

    for _, row in df.iterrows():
        stock = row['Stock']

        tick_buffer[stock].append({
            "price": row['Close'],
            "volume": row['Volume'],
            "time": now
        })

        if len(tick_buffer[stock]) > 300:
            tick_buffer[stock].pop(0)

# =============================
# CANDLES
# =============================
def build_candles():
    now = int(time.time())
    bucket = now - (now % CANDLE)

    for stock, ticks in tick_buffer.items():

        valid = [t for t in ticks if t['time'] >= bucket]
        if len(valid) < 2:
            continue

        prices = [t['price'] for t in valid]
        volumes = [t['volume'] for t in valid]

        candle = {
            "Stock": stock,
            "Open": prices[0],
            "High": max(prices),
            "Low": min(prices),
            "Close": prices[-1],
            "Volume": sum(volumes),
            "time": bucket
        }

        if len(candles_1m[stock]) == 0 or candles_1m[stock][-1]['time'] != bucket:
            candles_1m[stock].append(candle)

        if len(candles_1m[stock]) > 500:
            candles_1m[stock].pop(0)

# =============================
# BUILD DF
# =============================
def build_df():
    with lock:
        rows = []
        for stock in candles_1m:
            rows += candles_1m[stock]

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values(by=['Stock','time'])

    try:
        df = df.groupby('Stock', group_keys=False).apply(add_indicators).reset_index(drop=True)
    except Exception as e:
        print("INDICATOR ERROR:", e)
        return pd.DataFrame()

    return df.dropna()

# =============================
# TRADE MANAGEMENT
# =============================
def manage_trades(df):
    global equity

    for stock, pos in list(open_positions.items()):
        stock_df = df[df['Stock'] == stock]
        if stock_df.empty:
            continue

        latest = stock_df.iloc[-1]
        price = latest['Close']

        if price <= pos['stop'] or price >= pos['target']:

            pnl = (price - pos['entry']) * pos['size']
            equity += pnl
            equity_curve.append(equity)

            insert_trade(stock, pos['entry'], price, pnl, "WIN" if pnl>0 else "LOSS")
            update_weights()

            del open_positions[stock]

# =============================
# POSITION SIZE
# =============================
def calc_position_size(entry, stop):
    risk = 0.005 * equity
    diff = abs(entry - stop)
    return 0 if diff == 0 else risk / diff

# =============================
# SCAN
# =============================
def scan_logic():

    if not is_market_active():
        return []

    df = build_df()
    if df.empty:
        return []

    manage_trades(df)

    regime = detect_regime(df)
    params = adjust_parameters(regime, equity_curve)

    df_5m = resample_tf(df, '5T')
    df_15m = resample_tf(df, '15T')

    sector_strength = compute_sector_strength(df)
    latest = df.groupby('Stock').tail(1)

    results = []

    for _, row in latest.iterrows():

        stock = row['Stock']

        if stock in open_positions:
            continue

        if len(open_positions) >= MAX_POSITIONS:
            break

        if row['Volume'] < 20000:
            continue

        if stock not in sector_map:
            continue

        if sector_strength.get(sector_map[stock], 0) < -0.01:
            continue

        if row['Close'] <= row['EMA20']:
            continue

        if row['Volume'] < 1.2 * row['Vol_MA']:
            continue

        df5 = df_5m[df_5m['Stock']==stock]
        df15 = df_15m[df_15m['Stock']==stock]

        if df5.empty or df15.empty:
            continue

        t5 = get_trend(df5)
        t15 = get_trend(df15)

        if t5 <= 0 or t15 <= 0:
            continue

        if detect_accumulation(df[df['Stock']==stock]) == "DISTRIBUTION":
            continue

        score = compute_score(row)
        if score < params["score_threshold"]:
            continue

        entry, stop, target, rr = get_trade_levels(row)
        if rr < params["rr_threshold"]:
            continue

        size = calc_position_size(entry, stop)
        if size == 0:
            continue

        open_positions[stock] = {
            "entry": entry,
            "stop": stop,
            "target": target,
            "size": size
        }

        send_telegram(f"🚀 {stock} | Entry {entry:.2f} | TP {target:.2f}")

        results.append({
            "Stock": stock,
            "Score": round(score,2),
            "RR": round(rr,2),
            "Regime": regime
        })

    return results

# =============================
# ✅ RESTORED DASHBOARD
# =============================
@app.route('/')
def home():
    return """
    <html>
    <body style="background:#0f172a;color:white;font-family:sans-serif;">
        <h2>🚀 NEPSE AI TERMINAL</h2>
        <p>Status: RUNNING ✅</p>

        <h3>Endpoints:</h3>
        <ul>
            <li><a href="/scan" style="color:cyan;">/scan</a></li>
            <li><a href="/performance" style="color:cyan;">/performance</a></li>
        </ul>
    </body>
    </html>
    """

# =============================
# ROUTES
# =============================
@app.route('/scan')
def scan():
    return jsonify(scan_logic())

@app.route('/performance')
def performance():
    return jsonify({
        "equity": equity,
        "curve": equity_curve
    })   

# =============================
# LOOP
# =============================
def loop():
    while True:
        try:
            live = fetch_data()
            if not live.empty:
                with lock:
                    update_ticks(live)
                    build_candles()
        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(5)

threading.Thread(target=loop, daemon=True).start()

# =============================
# RUN
# =============================
import os

if __name__ == "__main__":
    print("🚀 FINAL SYSTEM READY")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
