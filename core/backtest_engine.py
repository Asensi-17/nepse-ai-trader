import pandas as pd

def run_backtest_engine(df, strategy_func):

    balance = 100000
    equity_curve = [balance]
    open_pos = None
    trades = []

    for i in range(50, len(df)):

        slice_df = df.iloc[:i+1]
        row = slice_df.iloc[-1]

        signal = strategy_func(slice_df)

        if open_pos is None and signal:

            entry, stop, target, rr = signal

            open_pos = {
                "entry": entry,
                "stop": stop,
                "target": target
            }

        elif open_pos:

            price = row['Close']

            if price <= open_pos['stop']:
                exit_price = open_pos['stop']
            elif price >= open_pos['target']:
                exit_price = open_pos['target']
            else:
                equity_curve.append(balance)
                continue

            pnl = exit_price - open_pos['entry']
            balance += pnl
            trades.append(pnl)
            open_pos = None

        equity_curve.append(balance)

    return {
        "final_balance": balance,
        "trades": len(trades),
        "winrate": sum(1 for t in trades if t>0)/len(trades) if trades else 0,
        "equity_curve": equity_curve
    }