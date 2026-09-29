"""
Streamlit dashboard for the Fitness Analytics case study.

Reads pre-cleaned data from fitness.db (built by etl.py) and renders a
glassmorphic, dark-theme dashboard with a left sidebar for navigation.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "fitness.db"

st.set_page_config(page_title="Fitness Analytics", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------- styling --
ACCENT = "#22c55e"
ACCENT_SOFT = "rgba(34, 197, 94, 0.18)"

st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}

    .stApp {{
        background: radial-gradient(circle at 15% 10%, #10201a 0%, #0b0f14 45%, #070a0d 100%);
        color: #e6f1ec;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(15, 22, 20, 0.85);
        border-right: 1px solid rgba(34, 197, 94, 0.15);
    }}

    section[data-testid="stSidebar"] .stButton button {{
        width: 100%;
        text-align: left;
        background: transparent;
        border: 1px solid transparent;
        color: #a9bcb4;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        margin-bottom: 4px;
        font-weight: 500;
        transition: all 0.15s ease;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: {ACCENT_SOFT};
        color: #ffffff;
        border-color: rgba(34, 197, 94, 0.4);
    }}

    .nav-active button {{
        background: {ACCENT_SOFT} !important;
        color: #ffffff !important;
        border-color: {ACCENT} !important;
    }}

    .glass-card {{
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        transition: border-color 0.2s ease, transform 0.2s ease;
        height: 100%;
    }}
    .glass-card:hover {{
        border-color: rgba(34, 197, 94, 0.45);
        transform: translateY(-2px);
    }}

    .kpi-label {{
        font-size: 0.8rem;
        color: #8fa39a;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.3rem;
    }}
    .kpi-value {{
        font-size: 1.9rem;
        font-weight: 700;
        color: #ffffff;
    }}
    .kpi-sub {{
        font-size: 0.8rem;
        color: {ACCENT};
        margin-top: 0.2rem;
    }}

    h1, h2, h3 {{
        color: #ffffff;
        font-weight: 650;
    }}

    .section-title {{
        border-left: 3px solid {ACCENT};
        padding-left: 0.6rem;
        margin: 1.4rem 0 0.8rem 0;
    }}
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
PLOT_BG = "rgba(0,0,0,0)"


def style_fig(fig):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#dce8e2"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
    return fig


# ------------------------------------------------------------------ data --
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    daily = pd.read_sql("SELECT * FROM daily_master", conn, parse_dates=["Date"])
    hourly = pd.read_sql("SELECT * FROM hourly", conn, parse_dates=["ActivityHour"])
    conn.close()
    return daily, hourly


daily, hourly = load_data()

# ------------------------------------------------------------------- nav --
PAGES = ["Overview", "Activity Trends", "Sleep", "Heart Rate", "Correlations", "Insights"]
if "page" not in st.session_state:
    st.session_state.page = "Overview"

st.sidebar.markdown("### Fitness Analytics")
st.sidebar.caption("Bellabeat-style case study")
st.sidebar.markdown("---")

for p in PAGES:
    active = st.session_state.page == p
    wrapper = st.sidebar.container()
    if wrapper.button(p, key=f"nav_{p}"):
        st.session_state.page = p

st.sidebar.markdown("---")
users = sorted(daily["Id"].unique())
user_filter = st.sidebar.multiselect("Filter by user ID", users, default=[])
date_min, date_max = daily["Date"].min(), daily["Date"].max()
date_range = st.sidebar.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)

view = daily.copy()
if user_filter:
    view = view[view["Id"].isin(user_filter)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    view = view[(view["Date"] >= start) & (view["Date"] <= end)]

page = st.session_state.page


def kpi(col, label, value, sub=None):
    with col:
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
        </div>
        """, unsafe_allow_html=True)


# --------------------------------------------------------------- Overview --
if page == "Overview":
    st.title("Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi(c1, "Users tracked", f"{view['Id'].nunique()}")
    kpi(c2, "Avg daily steps", f"{view['TotalSteps'].mean():,.0f}")
    kpi(c3, "Avg calories/day", f"{view['Calories'].mean():,.0f}")
    kpi(c4, "Avg sleep", f"{view['TotalMinutesAsleep'].mean()/60:.1f} hrs", "of users with sleep data")
    kpi(c5, "Device wear rate", f"{view['device_worn'].mean()*100:.0f}%")

    st.markdown('<div class="section-title"><h3>Steps over time</h3></div>', unsafe_allow_html=True)
    trend = view.groupby("Date", as_index=False)["TotalSteps"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["Date"], y=trend["TotalSteps"], mode="lines", fill="tozeroy",
        line=dict(color=ACCENT, width=2.5),
        fillcolor="rgba(34, 197, 94, 0.15)",
        hovertemplate="%{x|%b %d}<br>%{y:,.0f} steps<extra></extra>",
    ))
    if not trend.empty:
        peak = trend.loc[trend["TotalSteps"].idxmax()]
        fig.add_annotation(x=peak["Date"], y=peak["TotalSteps"], text=f"Peak: {peak['TotalSteps']:,.0f}",
                            showarrow=True, arrowhead=2, arrowcolor=ACCENT, font=dict(color=ACCENT))
    st.plotly_chart(style_fig(fig), use_container_width=True)

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="section-title"><h3>Activity minutes breakdown</h3></div>', unsafe_allow_html=True)
        minutes = view[["VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes", "SedentaryMinutes"]].mean()
        donut = go.Figure(data=[go.Pie(
            labels=["Very Active", "Fairly Active", "Lightly Active", "Sedentary"],
            values=minutes.values, hole=0.6,
            marker=dict(colors=[ACCENT, "#4ade80", "#86efac", "#374151"]),
        )])
        st.plotly_chart(style_fig(donut), use_container_width=True)
    with right:
        st.markdown('<div class="section-title"><h3>Calories distribution</h3></div>', unsafe_allow_html=True)
        hist = px.histogram(view, x="Calories", nbins=30, color_discrete_sequence=[ACCENT])
        st.plotly_chart(style_fig(hist), use_container_width=True)

# ---------------------------------------------------------- Activity Trends --
elif page == "Activity Trends":
    st.title("Activity Trends")
    metric = st.selectbox("Metric", ["TotalSteps", "Calories", "TotalDistance", "VeryActiveMinutes"])
    trend = view.groupby("Date", as_index=False)[metric].mean()
    fig = px.line(trend, x="Date", y=metric, markers=True, color_discrete_sequence=[ACCENT])
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown('<div class="section-title"><h3>Hourly pattern (avg across users)</h3></div>', unsafe_allow_html=True)
    hourly_view = hourly.copy()
    if user_filter:
        hourly_view = hourly_view[hourly_view["Id"].isin(user_filter)]
    hourly_view["Hour"] = hourly_view["ActivityHour"].dt.hour
    hourly_avg = hourly_view.groupby("Hour", as_index=False)["StepTotal"].mean()
    fig2 = px.bar(hourly_avg, x="Hour", y="StepTotal", color_discrete_sequence=[ACCENT])
    st.plotly_chart(style_fig(fig2), use_container_width=True)

# ------------------------------------------------------------------- Sleep --
elif page == "Sleep":
    st.title("Sleep")
    sleep_view = view.dropna(subset=["TotalMinutesAsleep"])
    if sleep_view.empty:
        st.info("No sleep data for the current filter selection.")
    else:
        c1, c2, c3 = st.columns(3)
        kpi(c1, "Avg time asleep", f"{sleep_view['TotalMinutesAsleep'].mean()/60:.1f} hrs")
        kpi(c2, "Avg time in bed", f"{sleep_view['TotalTimeInBed'].mean()/60:.1f} hrs")
        efficiency = (sleep_view["TotalMinutesAsleep"] / sleep_view["TotalTimeInBed"]).mean() * 100
        kpi(c3, "Sleep efficiency", f"{efficiency:.0f}%", "asleep vs. time in bed")

        trend = sleep_view.groupby("Date", as_index=False)[["TotalMinutesAsleep", "TotalTimeInBed"]].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["Date"], y=trend["TotalMinutesAsleep"], name="Asleep",
                                  line=dict(color=ACCENT, width=2.5)))
        fig.add_trace(go.Scatter(x=trend["Date"], y=trend["TotalTimeInBed"], name="In bed",
                                  line=dict(color="#6b7280", width=2, dash="dot")))
        st.plotly_chart(style_fig(fig), use_container_width=True)

# -------------------------------------------------------------- Heart Rate --
elif page == "Heart Rate":
    st.title("Heart Rate")
    hr_view = view.dropna(subset=["AvgHeartRate"])
    if hr_view.empty:
        st.info("No heart rate data for the current filter selection.")
    else:
        st.caption(f"Heart rate data is only available for {daily.dropna(subset=['AvgHeartRate'])['Id'].nunique()} "
                   f"of {daily['Id'].nunique()} users.")
        c1, c2, c3 = st.columns(3)
        kpi(c1, "Avg heart rate", f"{hr_view['AvgHeartRate'].mean():.0f} bpm")
        kpi(c2, "Avg min heart rate", f"{hr_view['MinHeartRate'].mean():.0f} bpm")
        kpi(c3, "Avg max heart rate", f"{hr_view['MaxHeartRate'].mean():.0f} bpm")

        trend = hr_view.groupby("Date", as_index=False)[["AvgHeartRate", "MinHeartRate", "MaxHeartRate"]].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["Date"], y=trend["MaxHeartRate"], name="Max", line=dict(color="#374151")))
        fig.add_trace(go.Scatter(x=trend["Date"], y=trend["AvgHeartRate"], name="Avg", line=dict(color=ACCENT, width=2.5)))
        fig.add_trace(go.Scatter(x=trend["Date"], y=trend["MinHeartRate"], name="Min", line=dict(color="#374151")))
        st.plotly_chart(style_fig(fig), use_container_width=True)

# ------------------------------------------------------------- Correlations --
elif page == "Correlations":
    st.title("Correlations")
    pairs = [
        ("TotalSteps", "Calories", "Steps vs. Calories burned"),
        ("TotalMinutesAsleep", "SedentaryMinutes", "Sleep vs. Sedentary minutes"),
        ("TotalSteps", "TotalMinutesAsleep", "Steps vs. Sleep"),
    ]
    cols = st.columns(3)
    for col, (x, y, title) in zip(cols, pairs):
        with col:
            sub = view.dropna(subset=[x, y])
            corr = sub[x].corr(sub[y]) if len(sub) > 2 else float("nan")
            st.markdown(f'<div class="section-title"><h4>{title}</h4></div>', unsafe_allow_html=True)
            fig = px.scatter(sub, x=x, y=y, trendline="ols", color_discrete_sequence=[ACCENT], opacity=0.6)
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption(f"correlation coefficient: {corr:.2f}")

# ------------------------------------------------------------------ Insights --
elif page == "Insights":
    st.title("Insights & Recommendations")
    st.markdown("""
    <div class="glass-card">
    <p><b>Key findings from the analysis:</b></p>
    <ul>
      <li>Users average <b>~7,600 steps/day</b> and <b>~2,300 calories/day</b>, with steps and calories
          moderately correlated (r &asymp; 0.59) &mdash; activity is a real driver of energy burn.</li>
      <li>Users are sedentary for <b>~16.5 hours/day on average</b>. Sleep duration and sedentary minutes
          are negatively correlated (r &asymp; -0.60): more sitting time tracks with less sleep.</li>
      <li>Devices were worn (steps &gt; 0) on <b>~92% of tracked days</b>, suggesting reasonably strong
          engagement with the tracker.</li>
      <li>Data coverage is uneven: all 33 users have activity data, but only 24 logged sleep, 14 have
          heart rate data, and just 8 logged weight &mdash; weight-based insights should be treated as
          directional only.</li>
    </ul>
    <p><b>Recommendations:</b></p>
    <ul>
      <li>Use in-app nudges to close the sedentary/sleep gap &mdash; e.g. an evening reminder to wind down
          when sedentary minutes run high, since that pattern tracks with shorter sleep.</li>
      <li>Since steps reliably predict calories burned, surface a simple "steps to calorie goal" widget to
          reinforce the habit loop.</li>
      <li>Encourage sleep and heart-rate tracking specifically (lowest adoption) with a short onboarding
          nudge, since those data sources are currently the weakest link in the dataset.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
