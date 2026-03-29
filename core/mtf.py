import pandas as pd

# =============================
# RESAMPLE TIMEFRAMES
# =============================
def resample_tf(df, timeframe):

    df = df.copy()
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.set_index('time')

    ohlc = df.groupby('Stock').resample(timeframe).agg({
        'Open':'first',
        'High':'max',
        'Low':'min',
        'Close':'last',
        'Volume':'sum'
    }).dropna().reset_index()

    return ohlc

# =============================
# TREND
# =============================
def get_trend(df):

    if len(df) < 20:
        return 0

    return (df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]