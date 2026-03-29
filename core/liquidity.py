import numpy as np

def liquidity_heatmap(df, bins=20):

    prices = df['Close']
    volumes = df['Volume']

    if len(prices) < 20:
        return []

    hist, edges = np.histogram(prices, bins=bins, weights=volumes)

    zones = []
    for i in range(len(hist)):
        if hist[i] > np.mean(hist):
            zones.append((edges[i], edges[i+1]))

    return zones