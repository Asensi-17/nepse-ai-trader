def detect_regime(df):

    if len(df) < 30:
        return "UNKNOWN"

    recent = df.tail(20)

    vol = (recent['High'] - recent['Low']).mean() / recent['Close'].mean()
    trend = (recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0]

    if vol < 0.004:
        return "LOW_VOL"

    if abs(trend) > 0.03:
        return "TRENDING"

    return "RANGING"