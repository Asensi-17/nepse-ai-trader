def orderflow_score(row):

    body = abs(row['Close'] - row['Open'])
    range_ = row['High'] - row['Low']

    if range_ == 0:
        return 0

    dominance = body / range_

    # bullish pressure
    if row['Close'] > row['Open']:
        return dominance

    # bearish pressure
    return -dominance