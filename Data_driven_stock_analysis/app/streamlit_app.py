import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Paths
OUTPUT_DIR = "C:/Users/LENOVO/Desktop/GUVI/Project/output"
SECTOR_CSV = "C:/Users/LENOVO/Desktop/GUVI/Project/data/sectors.csv"

# Background
st.markdown("""
    <style>
        .stApp {
            background-color: #f5f7fa;
        }
        .main-title {
            font-size: 32px;
            font-weight: 700;
            color: #1a237e;
            padding-bottom: 10px;
        }
        .section-title {
            font-size: 22px;
            font-weight: 600;
            color: #0d47a1;
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Nifty 50 Dashboard", layout="wide")
sns.set(style="whitegrid")

@st.cache_data
def load_data():
    master = pd.read_csv(os.path.join(OUTPUT_DIR, "clean_master.csv"), parse_dates=["date"])
    sectors = pd.read_csv(SECTOR_CSV)
    sectors.columns = sectors.columns.str.strip().str.title()
    return master, sectors

def compute_yearly_returns(master):
    yr = master.groupby("Ticker")["close"].agg(["first", "last"]).reset_index()
    yr["yearly_return"] = yr["last"] / yr["first"] - 1
    return yr

# Load data
master_df, sectors = load_data()
yr = compute_yearly_returns(master_df)

# Sidebar Navigation (Radio Buttons)
st.sidebar.title("Dashboard Menu")
menu = st.sidebar.radio(
    "Choose a visualization:",
    [
        "Market Summary",
        "Top 10 Gainers & Losers",
        "Volatility Analysis",
        "Cumulative Returns (Top 5)",
        "Sector-wise Performance",
        "Correlation Heatmap",
        "Monthly Gainers & Losers"
    ]
)

# -----------------------------
# 1. MARKET SUMMARY
# -----------------------------
if menu == "Market Summary":
    st.markdown('<div class="main-title">📊 Nifty 50 Stock Performance Dashboard</div>', unsafe_allow_html=True)

    green = int((yr["yearly_return"] > 0).sum())
    red = int((yr["yearly_return"] <= 0).sum())
    avg_price = float(master_df["close"].mean())
    avg_volume = float(master_df["volume"].mean())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Green Stocks", green)
    c2.metric("❌ Red Stocks", red)
    c3.metric("📈 Average Price", f"{avg_price:,.2f}")
    c4.metric("📊 Average Volume", f"{avg_volume:,.0f}")

# -----------------------------
# 2. TOP 10 GAINERS & LOSERS
# -----------------------------
elif menu == "Top 10 Gainers & Losers":
    st.markdown('<div class="section-title">🏆 Top 10 Gainers and Losers</div>', unsafe_allow_html=True)

    top10 = yr.sort_values("yearly_return", ascending=False).head(10)
    bottom10 = yr.sort_values("yearly_return", ascending=True).head(10)

    st.subheader("Top 10 Gainers")
    st.dataframe(top10)

    st.subheader("Top 10 Losers")
    st.dataframe(bottom10)

# -----------------------------
# 3. VOLATILITY ANALYSIS
# -----------------------------
elif menu == "Volatility Analysis":
    st.markdown('<div class="section-title">📈 Top 10 Most Volatile Stocks</div>', unsafe_allow_html=True)

    master_df["daily_return"] = master_df.groupby("Ticker")["close"].pct_change()
    vol = master_df.groupby("Ticker")["daily_return"].std().reset_index()
    vol = vol.rename(columns={"daily_return": "volatility"})
    top_vol = vol.sort_values("volatility", ascending=False).head(10)

    st.bar_chart(top_vol.set_index("Ticker"))

# -----------------------------
# 4. CUMULATIVE RETURNS
# -----------------------------
elif menu == "Cumulative Returns (Top 5)":
    st.markdown('<div class="section-title">📈 Cumulative Returns — Top 5 Performers</div>', unsafe_allow_html=True)

    master_df["daily_return"] = master_df.groupby("Ticker")["close"].pct_change()
    master_df["cum_return"] = (1 + master_df["daily_return"]).groupby(master_df["Ticker"]).cumprod() - 1

    top5 = master_df.groupby("Ticker")["cum_return"].last().sort_values(ascending=False).head(5).index.tolist()

    fig, ax = plt.subplots(figsize=(12, 6))
    for t in top5:
        sub = master_df[master_df["Ticker"] == t].sort_values("date")
        ax.plot(sub["date"], sub["cum_return"], label=t)

    ax.set_title("Cumulative Return Over Time")
    ax.set_ylabel("Cumulative Return")
    ax.legend()
    st.pyplot(fig)

# -----------------------------
# 5. SECTOR PERFORMANCE
# -----------------------------


elif menu == "Sector-wise Performance":

    st.markdown('<div class="section-title">🏭 Sector-wise Performance Breakdown</div>', unsafe_allow_html=True)

    # ✅ Clean column names
    sectors.columns = sectors.columns.str.strip().str.title()

    # ✅ Extract clean Symbol (important!)
    # Converts "ASIAN PAINTS: ASIANPAINT" → "ASIANPAINT"
    sectors["Symbol"] = sectors["Symbol"].str.split(":").str[-1].str.strip()

    # ✅ Clean sector names
    sectors["Sector"] = sectors["Sector"].str.strip().str.title()

    # ✅ Merge using Symbol (NOT Ticker)
    yr_sector = yr.merge(sectors, left_on="Ticker", right_on="Symbol", how="right")

    # ✅ Replace missing yearly returns with 0 (for sectors with no matching stocks)
    yr_sector["yearly_return"] = yr_sector["yearly_return"].fillna(0)

    # ✅ Calculate average yearly return per sector
    sector_avg = (
        yr_sector.groupby("Sector")["yearly_return"]
        .mean()
        .reset_index()
        .sort_values("yearly_return", ascending=False)
    )

    # ✅ Display total sectors
    st.write(f"✅ Total Sectors Found: {sector_avg['Sector'].nunique()}")

    # ✅ Show DataFrame
    st.subheader("📋 Sector-wise Average Yearly Return")
    st.dataframe(sector_avg)

    # ✅ Bar Chart
    st.subheader("📊 Average Yearly Return by Sector")
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.barplot(
        data=sector_avg,
        x="Sector",
        y="yearly_return",
        palette="viridis",
        ax=ax
    )
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Average Yearly Return")
    plt.title("Sector-wise Breakdown of Stock Performance")
    st.pyplot(fig)




    
# -----------------------------
# 6. CORRELATION HEATMAP
# -----------------------------
elif menu == "Correlation Heatmap":
    st.markdown('<div class="section-title">🔥 Correlation Heatmap (Returns)</div>', unsafe_allow_html=True)

    pivot_close = master_df.pivot_table(index="date", columns="Ticker", values="close")
    corr = pivot_close.pct_change().corr()

    st.dataframe(corr.style.background_gradient(cmap="coolwarm"))

# -----------------------------
# 7. MONTHLY GAINERS & LOSERS
# -----------------------------
elif menu == "Monthly Gainers & Losers":
    st.markdown('<div class="section-title">📅 Monthly Top 5 Gainers and Losers</div>', unsafe_allow_html=True)

    monthly = master_df.groupby(["Ticker", "month"])["close"].agg(["first", "last"]).reset_index()
    monthly["monthly_return"] = monthly["last"] / monthly["first"] - 1

    months = sorted(monthly["month"].unique())
    selected_month = st.selectbox("Select Month", months)

    sub = monthly[monthly["month"] == selected_month]
    gainers = sub.sort_values("monthly_return", ascending=False).head(5)
    losers = sub.sort_values("monthly_return", ascending=True).head(5)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 5 Gainers")
        st.bar_chart(gainers.set_index("Ticker")["monthly_return"])

    with c2:
        st.subheader("Top 5 Losers")
        st.bar_chart(losers.set_index("Ticker")["monthly_return"])

st.caption("Data source: per-ticker CSVs; all metrics computed from daily closes.")