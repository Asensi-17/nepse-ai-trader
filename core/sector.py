# =============================
# DYNAMIC SECTOR DETECTION
# =============================

# You can expand this gradually
sector_map = {
    "NABIL": "BANKING",
    "KBL": "BANKING",
    "NICA": "BANKING",

    "UPPER": "HYDRO",
    "HIDCL": "HYDRO",
    "NHPC": "HYDRO",

    "CFCL": "FINANCE",
    "NFS": "FINANCE"
}

# =============================
# SECTOR STRENGTH CALCULATION
# =============================
def compute_sector_strength(df):

    sector_perf = {}

    for stock in df['Stock'].unique():

        if stock not in sector_map:
            continue

        sector = sector_map[stock]
        sub = df[df['Stock'] == stock]

        if len(sub) < 5:
            continue

        change = (
            sub['Close'].iloc[-1] - sub['Close'].iloc[-5]
        ) / sub['Close'].iloc[-5]

        sector_perf.setdefault(sector, []).append(change)

    # average sector strength
    return {
        s: sum(v)/len(v)
        for s, v in sector_perf.items()
        if len(v) > 0
    }