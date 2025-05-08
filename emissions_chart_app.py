import streamlit as st
import pandas as pd
import plotly.express as px

# Constants
SCALING_FACTOR = 1e6
MIGRATION_AMOUNT = 3750000 # Airdrop amount from testnet migration
B3TR_CAP = 1000243154
INITIAL_X_APP_ALLOCATION = 2000000
GM_NFT_START_ROUND = 46 

# Streamlit app settings
st.set_page_config(page_title="B3TR Emissions Simulator", layout="wide")
st.title("📊 B3TR Emissions Simulator")

st.sidebar.header("Decay Settings")
x_allocations_decay = st.sidebar.slider("XAllocations Decay (%)", 0, 100, 4)
x_allocations_decay_period = st.sidebar.slider("XAllocations Decay Period (cycles)", 1, 1000, 12)
vote2earn_decay = st.sidebar.slider("Vote2Earn Decay (%)", 0, 100, 20)
vote2earn_decay_period = st.sidebar.slider("Vote2Earn Decay Period (cycles)", 1, 100, 50)
max_vote2earn_decay = st.sidebar.slider("Max Vote2Earn Decay (%)", 0, 100, 80)
treasury_percentage = st.sidebar.slider("Treasury Percentage (%)", 0, 100, 25) * 100
gm_nft_percentage = st.sidebar.slider("GM-NFT Share of Treasury (%)", 0, 100, 25)

# Decay logic
def calculate_vote2earn_decay_percentage(cycle):
    if cycle <= 1:
        return 0
    decay_periods = (cycle - 1) // vote2earn_decay_period
    decay = vote2earn_decay * decay_periods
    return min(decay, max_vote2earn_decay)

def calculate_next_x_allocation(cycle, last_allocation):
    if cycle < 2:
        return INITIAL_X_APP_ALLOCATION
    if (cycle - 1) % x_allocations_decay_period == 0:
        last_allocation *= (1 - x_allocations_decay / 100)
    return round(last_allocation, 6)

# Emissions simulation
# Add bootstrap cycle (cycle 1)
data = []
cycle = 2  # Start from cycle 2 since cycle 1 is bootstrapped manually
total_emissions = 0
# Simulate bootstrap emissions for cycle 1
bootstrap_x_allocation = INITIAL_X_APP_ALLOCATION
bootstrap_vote2earn = bootstrap_x_allocation  # Initially same
bootstrap_treasury = round((bootstrap_x_allocation + bootstrap_vote2earn) * (treasury_percentage / 10000), 6)
bootstrap_gm_nft = 0

bootstrap_total = bootstrap_x_allocation + bootstrap_vote2earn + bootstrap_treasury + bootstrap_gm_nft
total_emissions = bootstrap_total

data.append({
    "Cycle": 1,
    "XAllocations": bootstrap_x_allocation,
    "Vote2Earn": bootstrap_vote2earn,
    "Treasury": bootstrap_treasury,
    "GM-NFT": bootstrap_gm_nft,
    "Total": bootstrap_total,
    "Cumulative": total_emissions
})

last_x_allocation = INITIAL_X_APP_ALLOCATION

while True:
    x_allocation = calculate_next_x_allocation(cycle, last_x_allocation)
    last_x_allocation = x_allocation
    vote2earn_decay_pct = calculate_vote2earn_decay_percentage(cycle)
    vote2earn = round(x_allocation * (1 - vote2earn_decay_pct / 100), 6)
    treasury = round((x_allocation + vote2earn) * (treasury_percentage / 10000), 6)

    gm_nft = 0
    if cycle >= GM_NFT_START_ROUND:
        gm_nft = round(treasury * (gm_nft_percentage / 100), 6)
        treasury -= gm_nft

    cycle_total = x_allocation + vote2earn + treasury + gm_nft

    if total_emissions + cycle_total + MIGRATION_AMOUNT > B3TR_CAP:
        # Stop before next cycle if adding would exceed cap
        break

    total_emissions += cycle_total

    data.append({
        "Cycle": cycle,
        "XAllocations": x_allocation,
        "Vote2Earn": vote2earn,
        "Treasury": treasury,
        "GM-NFT": gm_nft,
        "Total": cycle_total,
        "Cumulative": total_emissions
    })

    cycle += 1

df = pd.DataFrame(data)

# Line chart
fig = px.line(df, x="Cycle", y=["XAllocations", "Vote2Earn", "Treasury", "GM-NFT"],
              labels={"value": "B3TR Emissions", "variable": "Pool"},
              title="Emissions Per Pool Over Time")
fig.update_layout(legend_title_text='Pool')

st.plotly_chart(fig, use_container_width=True)

# Cycle selector for cumulative pool stats
selected_cycle = st.sidebar.slider("Select Cycle to View Cumulative Emissions", 1, len(df), len(df))
df_selected = df[df["Cycle"] <= selected_cycle]

# Per-cycle emissions and % for the selected cycle
st.subheader(f"📆 Cycle {selected_cycle} Emission Breakdown")
row = df[df["Cycle"] == selected_cycle].iloc[0]
cycle_total = row["Total"]

def pct_of_cycle(val):
    return f"{(val / cycle_total) * 100:.2f}%"

col5, col6, col7, col8 = st.columns(4)
col5.metric("XAllocations (Cycle)", f"{int(row['XAllocations']):,} B3TR", pct_of_cycle(row['XAllocations']))
col6.metric("Vote2Earn (Cycle)", f"{int(row['Vote2Earn']):,} B3TR", pct_of_cycle(row['Vote2Earn']))
col7.metric("Treasury (Cycle)", f"{int(row['Treasury']):,} B3TR", pct_of_cycle(row['Treasury']))
col8.metric("GM-NFT (Cycle)", f"{int(row['GM-NFT']):,} B3TR", pct_of_cycle(row['GM-NFT']))

# Total emissions to date per pool
total_x = df_selected["XAllocations"].sum()
total_v2e = df_selected["Vote2Earn"].sum()
total_treasury = df_selected["Treasury"].sum()
total_gm_nft = df_selected["GM-NFT"].sum()
total_all = total_x + total_v2e + total_treasury + total_gm_nft + MIGRATION_AMOUNT

def pct(val):
    return f"{(val / total_all) * 100:.2f}%"
total_v2e = df_selected["Vote2Earn"].sum()
total_treasury = df_selected["Treasury"].sum()
total_gm_nft = df_selected["GM-NFT"].sum()

st.subheader(f"🚀 Emissions Totals Up to Cycle {selected_cycle}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("XAllocations", f"{int(total_x):,} B3TR", pct(total_x))
col2.metric("Vote2Earn", f"{int(total_v2e):,} B3TR", pct(total_v2e))
col3.metric("Treasury", f"{int(total_treasury):,} B3TR", pct(total_treasury))
col4.metric("GM-NFT", f"{int(total_gm_nft):,} B3TR", pct(total_gm_nft))



# Show total emissions to date
st.metric("Total B3TR Supply (All Pools + Migration)", f"{int(total_x + total_v2e + total_treasury + total_gm_nft + MIGRATION_AMOUNT):,} B3TR")

