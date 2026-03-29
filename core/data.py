import pandas as pd
import requests

def fetch_nepse_data():
    url = "https://www.nepalstock.com/api/nots/nepse-data"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        df = pd.DataFrame(data)

        df.rename(columns={
            "symbol": "Stock",
            "openPrice": "Open",
            "highPrice": "High",
            "lowPrice": "Low",
            "closePrice": "Close",
            "totalTradedQuantity": "Volume"
        }, inplace=True)

        df = df[['Stock','Open','High','Low','Close','Volume']]

        return df

    except Exception as e:
        print("DATA ERROR:", e)
        return pd.DataFrame()


def preprocess(df):
    df = df.dropna()
    df = df[df['Close'] > 0]
    return df