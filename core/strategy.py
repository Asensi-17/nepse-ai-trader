performance_db = {
    "trades": [],
    "factors": {
        "trend": {"weight": 0.2, "wins": 1, "losses": 1},
        "momentum": {"weight": 0.15, "wins": 1, "losses": 1},
        "volume": {"weight": 0.15, "wins": 1, "losses": 1},
        "ob": {"weight": 0.2, "wins": 1, "losses": 1},
        "fvg": {"weight": 0.15, "wins": 1, "losses": 1},
        "liq": {"weight": 0.15, "wins": 1, "losses": 1}
    }
}

# =============================
# UPDATE AI WEIGHTS
# =============================
def update_weights():

    for k, v in performance_db["factors"].items():

        total = v["wins"] + v["losses"]
        winrate = v["wins"] / total

        # adaptive weight
        v["weight"] = max(0.05, min(0.4, winrate))

# =============================
# SCORE
# =============================
def compute_score(row):

    f = performance_db["factors"]
    score = 0

    if row['EMA20'] > row['EMA50']:
        score += f["trend"]["weight"]

    if row['RSI'] > 55:
        score += f["momentum"]["weight"]

    if row['Volume'] > row['Vol_MA']:
        score += f["volume"]["weight"]

    if row.get('bull_ob'):
        score += f["ob"]["weight"]

    if row.get('fvg_up'):
        score += f["fvg"]["weight"]

    if row.get('equal_low'):
        score += f["liq"]["weight"]

    return round(score, 2)


# =============================
# TRADE LEVELS
# =============================
def get_trade_levels(row):

    atr = row['ATR']

    entry = row['Close'] * 1.003

    stop = entry - 1.5 * atr
    target = entry + 3 * atr

    rr = (target-entry)/(entry-stop) if (entry-stop)!=0 else 0

    return entry, stop, target, rr