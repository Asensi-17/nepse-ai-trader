from core.backtest import run_backtest

def optimize(df):

    best = None
    best_score = -999

    for score_threshold in [0.7, 0.75, 0.8, 0.85]:
        result = run_backtest(df, score_threshold)

        score = result["pnl"]

        if score > best_score:
            best_score = score
            best = {
                "score_threshold": score_threshold,
                "result": result
            }

    return best