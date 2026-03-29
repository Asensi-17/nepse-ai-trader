def detect_accumulation(df):

    if len(df) < 20:
        return "NONE"

    recent = df.tail(15)

    high = recent['High'].max()
    low = recent['Low'].min()

    range_pct = (high - low) / low

    avg_vol = recent['Volume'].mean()

    # tight range + rising volume = accumulation
    if range_pct < 0.03 and recent['Volume'].iloc[-1] > avg_vol:
        return "ACCUMULATION"

    # distribution (top range)
    if range_pct < 0.03 and recent['Close'].iloc[-1] < recent['Open'].iloc[-1]:
        return "DISTRIBUTION"

    return "NONE"