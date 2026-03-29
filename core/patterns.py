import numpy as np

# =============================
# ORDER BLOCK (REAL SMC)
# =============================
def detect_order_blocks(df):

    df['bull_ob'] = False
    df['bear_ob'] = False

    for i in range(3, len(df)):

        move = (df['Close'].iloc[i] - df['Open'].iloc[i-1]) / df['Open'].iloc[i-1]

        # bullish OB = last bearish candle before strong up move
        if move > 0.025 and df['Close'].iloc[i-1] < df['Open'].iloc[i-1]:
            df.loc[df.index[i-1], 'bull_ob'] = True

        # bearish OB
        if move < -0.025 and df['Close'].iloc[i-1] > df['Open'].iloc[i-1]:
            df.loc[df.index[i-1], 'bear_ob'] = True

    return df


# =============================
# FAIR VALUE GAP (FVG)
# =============================
def detect_fvg(df):

    df['fvg_up'] = False
    df['fvg_down'] = False

    for i in range(2, len(df)):

        # bullish gap
        if df['Low'].iloc[i] > df['High'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_up'] = True

        # bearish gap
        if df['High'].iloc[i] < df['Low'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_down'] = True

    return df


# =============================
# LIQUIDITY POOLS
# =============================
def detect_liquidity(df):

    df['equal_high'] = False
    df['equal_low'] = False

    for i in range(3, len(df)):

        highs = df['High'].iloc[i-3:i]
        lows = df['Low'].iloc[i-3:i]

        if abs(max(highs) - min(highs)) / df['Close'].iloc[i] < 0.002:
            df.loc[df.index[i], 'equal_high'] = True

        if abs(max(lows) - min(lows)) / df['Close'].iloc[i] < 0.002:
            df.loc[df.index[i], 'equal_low'] = True

    return df


# =============================
# PREMIUM / DISCOUNT
# =============================
def detect_pd_zones(df):

    df['premium'] = False
    df['discount'] = False

    for i in range(20, len(df)):
        high = df['High'].iloc[i-20:i].max()
        low = df['Low'].iloc[i-20:i].min()

        mid = (high + low) / 2

        if df['Close'].iloc[i] > mid:
            df.loc[df.index[i], 'premium'] = True
        else:
            df.loc[df.index[i], 'discount'] = True

    return df