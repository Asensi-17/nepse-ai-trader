import pandas as pd
from core.strategy import compute_score, get_trade_levels

def run_backtest(df, score_threshold=0.8):

    balance = 100000
    trades = []
    open_pos = None

    df = df.copy()

    for i in range(50, len(df)):

        row = df.iloc[i]

        # skip if indicators not ready
        if pd.isna(row['ATR']) or pd.isna(row['RSI']):
            continue

        if open_pos is None:

            score = compute_score(row)

            if score >= score_threshold:

                entry, stop, target, rr = get_trade_levels(row)

                if rr >= 1.8:
                    open_pos = {
                        "entry": entry,
                        "stop": stop,
                        "target": target
                    }

        else:
            price = row['Close']

            if price <= open_pos['stop']:
                pnl = open_pos['stop'] - open_pos['entry']
                balance += pnl
                trades.append(pnl)
                open_pos = None

            elif price >= open_pos['target']:
                pnl = open_pos['target'] - open_pos['entry']
                balance += pnl
                trades.append(pnl)
                open_pos = None

    winrate = sum(1 for t in trades if t > 0) / len(trades) if trades else 0

    return {
        "final_balance": balance,
        "trades": len(trades),
        "winrate": round(winrate, 2),
        "pnl": sum(trades)
    }