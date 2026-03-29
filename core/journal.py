trade_journal = []

def log_trade(stock, entry, exit_price, pnl):

    result = "WIN" if pnl > 0 else "LOSS"

    trade_journal.append({
        "stock": stock,
        "entry": entry,
        "exit": exit_price,
        "pnl": round(pnl,2),
        "result": result
    })

def get_journal():
    return trade_journal