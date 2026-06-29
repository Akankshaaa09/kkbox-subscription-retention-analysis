# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard — Redesigned
# Author: Akanksha Nayak
# ============================================================
from pathlib import Path
import gdown
import os

DB_PATH = Path("data/kkbox.db")
if not DB_PATH.exists():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading database...")
    gdown.download(
        "https://drive.google.com/uc?id=1RExff-WGtouE_yMtAWcQR0_hPvYjIpw8",
        str(DB_PATH),
        quiet=False
    )
    print("Done!")

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="KKBox Churn Analysis",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Design tokens ──
BG       = "#0A0A0A"
SURFACE  = "#111111"
SURFACE2 = "#1A1A1A"
SURFACE3 = "#222222"
BORDER   = "#2E2E2E"
GREEN    = "#00C48C"
RED      = "#FF4D4D"
AMBER    = "#FFB547"
TEXT     = "#F2F2F2"
MUTED    = "#777777"
ACCENT   = "#7B61FF"
DIM      = "#444444"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Inter', sans-serif;
      background-color: {BG};
      color: {TEXT};
  }}
  .stApp {{ background-color: {BG}; }}
  .block-container {{ padding-top: 0 !important; max-width: 1200px; }}

  /* ── Tab navigation — BIG and obvious ── */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 0px;
      background: {SURFACE};
      padding: 0;
      border-radius: 0;
      border: none;
      border-bottom: 2px solid {BORDER};
      margin-bottom: 32px;
  }}
  .stTabs [data-baseweb="tab"] {{
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      font-weight: 500;
      color: {MUTED};
      background: transparent;
      border-radius: 0;
      padding: 16px 28px;
      border: none;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      letter-spacing: 0.01em;
  }}
  .stTabs [aria-selected="true"] {{
      background: transparent !important;
      color: {TEXT} !important;
      border-bottom: 3px solid {GREEN} !important;
      font-weight: 600 !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{
      color: {TEXT} !important;
  }}

  /* ── Metrics ── */
  div[data-testid="metric-container"] {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 10px;
      padding: 20px 22px;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important;
      font-size: 11px !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.1em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {TEXT} !important;
      font-family: 'Space Grotesk', sans-serif !important;
      font-size: 26px !important;
      font-weight: 700 !important;
  }}

  hr {{ border-color: {BORDER} !important; margin: 28px 0 !important; }}
  h1, h2, h3 {{
      font-family: 'Space Grotesk', sans-serif !important;
      color: {TEXT} !important;
  }}

  .section-label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: {MUTED};
      margin-bottom: 6px;
  }}
  .chart-title {{
      font-family: 'Space Grotesk', sans-serif;
      font-size: 15px;
      font-weight: 600;
      color: {TEXT};
      margin-bottom: 4px;
  }}
  .chart-sub {{
      font-size: 12px;
      color: {MUTED};
      margin-bottom: 16px;
      line-height: 1.5;
  }}
  .insight-box {{
      background: {SURFACE2};
      border-left: 3px solid {GREEN};
      border-radius: 0 8px 8px 0;
      padding: 14px 18px;
      margin: 12px 0;
      font-size: 13px;
      color: {TEXT};
      line-height: 1.6;
  }}
  .stat-pill {{
      display: inline-block;
      background: {SURFACE3};
      border: 1px solid {BORDER};
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 12px;
      font-weight: 600;
      color: {TEXT};
      margin: 3px 3px;
  }}
</style>
""", unsafe_allow_html=True)

DB_PATH     = Path("data/kkbox.db")
ASSETS_PATH = Path("assets")

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

def chart(fig, height=None):
    if height:
        fig.update_layout(height=height)
    fig.update_layout(
        plot_bgcolor=SURFACE2,
        paper_bgcolor=SURFACE,
        font_color=TEXT,
        font_family="Inter",
        title_font_family="Space Grotesk",
        title_font_size=14,
        margin=dict(t=20, b=20, l=10, r=10),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont_color=MUTED),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont_color=MUTED),
        legend=dict(bgcolor=SURFACE2, bordercolor=BORDER,
                    borderwidth=1, font_color=TEXT)
    )
    return fig

# ════════════════════════════════════════════════════════
# QUERIES
# ════════════════════════════════════════════════════════
QUERY_OVERVIEW = """
    SELECT
        COUNT(*)                                    AS total_users,
        ROUND(AVG(is_churn) * 100, 2)              AS churn_rate_pct,
        ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) AS avg_rev_retained,
        ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) AS avg_rev_churned,
        ROUND(AVG(tenure_days),0)                  AS avg_tenure
    FROM users
"""
QUERY_AUTORENEW = """
    SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew ON' ELSE 'Auto-renew OFF' END AS status,
           COUNT(*) AS users, ROUND(AVG(is_churn)*100,2) AS churn_pct
    FROM users WHERE is_auto_renew IS NOT NULL GROUP BY is_auto_renew ORDER BY is_auto_renew DESC
"""
QUERY_PLAN = """
    SELECT payment_plan_days, COUNT(*) AS users,
           ROUND(AVG(is_churn)*100,2) AS churn_pct,
           ROUND(AVG(actual_amount_paid),2) AS avg_paid
    FROM users WHERE payment_plan_days IN (7,30,90,180,365)
    GROUP BY payment_plan_days ORDER BY payment_plan_days
"""
QUERY_RISK = """
    SELECT risk_tier, COUNT(*) AS users,
           ROUND(AVG(churn_probability)*100,1) AS avg_prob,
           ROUND(AVG(actual_churn)*100,1) AS actual_churn_pct,
           ROUND(AVG(plan_list_price),2) AS avg_price,
           ROUND(SUM(churn_probability*plan_list_price),0) AS rev_at_risk
    FROM risk_scores GROUP BY risk_tier ORDER BY avg_prob DESC
"""
QUERY_COHORT = """
    SELECT cohort, cohort_size, retained, retention_rate
    FROM cohort_retention WHERE cohort >= '2015-01' ORDER BY cohort
"""
QUERY_REG = """
    SELECT registered_via, COUNT(*) AS users,
           ROUND(AVG(is_churn)*100,2) AS churn_pct
    FROM users WHERE registered_via IS NOT NULL
    GROUP BY registered_via ORDER BY churn_pct DESC
"""
QUERY_ROI = "SELECT * FROM roi_summary LIMIT 1"

# ════════════════════════════════════════════════════════
# HERO SECTION
# ════════════════════════════════════════════════════════
overview = run_query(QUERY_OVERVIEW).iloc[0]

st.markdown(f"""
<div style='background:{SURFACE}; border-bottom:1px solid {BORDER};
            padding:40px 48px 36px; margin:-80px -80px 40px -80px;'>
  <div class='section-label'>Portfolio Project · Music Streaming Analytics</div>
  <div style='font-family:Space Grotesk,sans-serif; font-size:2rem;
              font-weight:700; color:{TEXT}; line-height:1.25; margin:10px 0 16px'>
    KKBox Subscription Retention<br>& Churn Analysis
  </div>
  <div style='font-size:13px; color:{MUTED}; max-width:600px; line-height:1.7; margin-bottom:24px'>
    Retention analysis across <b style='color:{TEXT}'>970,960 subscribers</b> on Asia's
    leading music streaming platform. Built to answer: who is churning, why are they
    leaving, and which users should we act on first?
  </div>
  <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:28px'>
    <span class='stat-pill'>Python</span>
    <span class='stat-pill'>SQL</span>
    <span class='stat-pill'>XGBoost</span>
    <span class='stat-pill'>SHAP</span>
    <span class='stat-pill'>Streamlit</span>
    <span class='stat-pill' style='border-color:{GREEN}; color:{GREEN}'>AUC 0.9876</span>
    <span class='stat-pill' style='border-color:{ACCENT}; color:{ACCENT}'>5-fold CV ± 0.0003</span>
  </div>
  <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:16px; max-width:800px'>
    <div style='border-left:3px solid {GREEN}; padding-left:14px'>
      <div style='font-size:11px; color:{MUTED}; text-transform:uppercase;
                  letter-spacing:0.1em; font-weight:600'>Users Analysed</div>
      <div style='font-family:Space Grotesk; font-size:22px; font-weight:700;
                  color:{TEXT}'>{int(overview['total_users']):,}</div>
    </div>
    <div style='border-left:3px solid {RED}; padding-left:14px'>
      <div style='font-size:11px; color:{MUTED}; text-transform:uppercase;
                  letter-spacing:0.1em; font-weight:600'>Churn Rate</div>
      <div style='font-family:Space Grotesk; font-size:22px; font-weight:700;
                  color:{TEXT}'>{overview['churn_rate_pct']}%</div>
    </div>
    <div style='border-left:3px solid {AMBER}; padding-left:14px'>
      <div style='font-size:11px; color:{MUTED}; text-transform:uppercase;
                  letter-spacing:0.1em; font-weight:600'>Avg Rev · Retained</div>
      <div style='font-family:Space Grotesk; font-size:22px; font-weight:700;
                  color:{TEXT}'>TWD {overview['avg_rev_retained']:,.0f}</div>
    </div>
    <div style='border-left:3px solid {ACCENT}; padding-left:14px'>
      <div style='font-size:11px; color:{MUTED}; text-transform:uppercase;
                  letter-spacing:0.1em; font-weight:600'>Avg Rev · Churned</div>
      <div style='font-family:Space Grotesk; font-size:22px; font-weight:700;
                  color:{RED}'>TWD {overview['avg_rev_churned']:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Key finding callout
st.markdown(f"""
<div style='background:{SURFACE2}; border:1px solid {BORDER};
            border-left:4px solid {GREEN}; border-radius:0 10px 10px 0;
            padding:16px 20px; margin-bottom:32px'>
  <span style='font-size:11px; font-weight:600; text-transform:uppercase;
               letter-spacing:0.1em; color:{GREEN}'>Key Finding</span>
  <div style='font-size:14px; color:{TEXT}; margin-top:4px; line-height:1.6'>
    Churned users paid <b style='color:{RED}'>3× more</b> than retained users
    (TWD {overview['avg_rev_churned']:,.0f} vs TWD {overview['avg_rev_retained']:,.0f}).
    Auto-renew OFF users churn at <b style='color:{RED}'>30.6%</b> vs
    <b style='color:{GREEN}'>3.8%</b> for auto-renew ON — an 8× gap.
    <b style='color:{TEXT}'>Churn here is a payments problem, not an engagement problem.</b>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Cohort Retention",
    "🔍  Churn Drivers",
    "🎯  Risk Scoring",
    "🧪  Model Validation",
    "💡  Recommendations"
])

# ── TAB 1: Cohort Retention ──
with tab1:
    cohort_df = run_query(QUERY_COHORT)
    avg_ret   = cohort_df['retention_rate'].mean()

    st.markdown(f"<div class='chart-title'>Monthly Cohort Retention Rates</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-sub'>Each row is one month of signups. Colour shows retention: red = below average ({avg_ret:.1f}%), green = above average.</div>", unsafe_allow_html=True)

    # Split into two columns so chart isn't one massive scroll
    mid = len(cohort_df) // 2
    c1, c2 = st.columns(2)

    with c1:
        df1 = cohort_df.iloc[mid:].copy()
        fig = px.bar(df1, x="retention_rate", y="cohort", orientation='h',
                     color="retention_rate",
                     color_continuous_scale=[[0,RED],[0.5,AMBER],[1,GREEN]],
                     text=df1['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                     labels={"retention_rate":"Retention (%)","cohort":""},
                     height=480)
        fig.update_traces(textposition='outside', textfont_size=10)
        fig.update_layout(coloraxis_showscale=False, xaxis_range=[80,102],
                          yaxis={'categoryorder':'category ascending'})
        st.plotly_chart(chart(fig), use_container_width=True)

    with c2:
        df2 = cohort_df.iloc[:mid].copy()
        fig2 = px.bar(df2, x="retention_rate", y="cohort", orientation='h',
                      color="retention_rate",
                      color_continuous_scale=[[0,RED],[0.5,AMBER],[1,GREEN]],
                      text=df2['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                      labels={"retention_rate":"Retention (%)","cohort":""},
                      height=480)
        fig2.update_traces(textposition='outside', textfont_size=10)
        fig2.update_layout(coloraxis_showscale=False, xaxis_range=[80,102],
                           yaxis={'categoryorder':'category ascending'})
        st.plotly_chart(chart(fig2), use_container_width=True)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Average Retention Rate",  f"{avg_ret:.1f}%")
    m2.metric("Best Cohort",
              f"{cohort_df.loc[cohort_df['retention_rate'].idxmax(),'cohort']}",
              f"{cohort_df['retention_rate'].max():.1f}%")
    m3.metric("Cohorts Tracked", f"{len(cohort_df)}")

    st.markdown(f"""
    <div class='insight-box'>
    <b>What this tells us:</b> Retention is broadly stable across cohorts at 85–94%,
    with no dramatic deterioration over time. The variation isn't random —
    it correlates with acquisition channel mix in those months, which is explored in the next tab.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2: Churn Drivers ──
with tab2:
    st.markdown(f"""
    <div class='insight-box' style='border-color:{AMBER}; margin-bottom:24px'>
    <b>The central finding:</b> Churned users listened just as much as retained users
    before leaving. Listening metrics (total seconds, completion rate, active days)
    barely register in the model. The dominant signals are all payment-related —
    meaning product improvements won't fix churn. Subscription management will.
    </div>
    """, unsafe_allow_html=True)

    # Auto-renew vs plan length
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-title'>Churn Rate by Auto-Renew Status</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>The single strongest signal in the dataset — an 8× difference.</div>", unsafe_allow_html=True)
        auto_df = run_query(QUERY_AUTORENEW)
        fig3 = px.bar(auto_df, x="status", y="churn_pct",
                      color="status",
                      color_discrete_map={"Auto-renew ON":GREEN, "Auto-renew OFF":RED},
                      text=auto_df['churn_pct'].apply(lambda x: f"{x}%"),
                      labels={"churn_pct":"Churn Rate (%)","status":""},
                      height=320)
        fig3.update_traces(textposition='outside', textfont_size=14,
                           textfont_color=TEXT, width=0.4)
        fig3.update_layout(showlegend=False, yaxis_range=[0,38])
        st.plotly_chart(chart(fig3), use_container_width=True)

    with col2:
        st.markdown("<div class='chart-title'>Churn Rate by Plan Length</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Longer discounted plans attract lower-loyalty subscribers — counter-intuitive but consistent.</div>", unsafe_allow_html=True)
        plan_df = run_query(QUERY_PLAN)
        plan_df['label'] = plan_df['payment_plan_days'].apply(
            lambda x: {7:"7 days",30:"30 days",90:"3 months",
                       180:"6 months",365:"1 year"}.get(int(x),f"{int(x)}d"))
        fig4 = px.bar(plan_df, x="label", y="churn_pct",
                      color="churn_pct",
                      color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                      text=plan_df['churn_pct'].apply(lambda x: f"{x}%"),
                      labels={"churn_pct":"Churn Rate (%)","label":""},
                      height=320)
        fig4.update_traces(textposition='outside', textfont_size=13,
                           textfont_color=TEXT)
        fig4.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart(fig4), use_container_width=True)

    st.divider()

    # SHAP + Registration channel
    col3, col4 = st.columns([3,2])

    with col3:
        st.markdown("<div class='chart-title'>What Drives Churn — SHAP Feature Importance</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Payment method, plan price, and registration channel dominate. Listening metrics (total_secs, completion_rate, avg_secs_per_day) are near zero — confirming churn is not an engagement problem.</div>", unsafe_allow_html=True)
        st.image(str(ASSETS_PATH / "shap_importance.png"), use_column_width=True)

    with col4:
        st.markdown("<div class='chart-title'>Churn Rate by Acquisition Channel</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chart-sub'>Channel 4 churns at 23% — over 5× higher than Channel 7 (4.5%). These are platform registration methods per KKBox's internal channel taxonomy.</div>", unsafe_allow_html=True)
        reg_df = run_query(QUERY_REG)
        reg_df['channel'] = reg_df['registered_via'].apply(
    lambda x: f"Channel {int(x)}")
        fig5 = px.bar(reg_df, x="channel", y="churn_pct",
                      color="churn_pct",
                      color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                      text=reg_df['churn_pct'].apply(lambda x: f"{x:.1f}%"),
                      labels={"churn_pct":"Churn (%)","channel":""},
                      height=360)
        fig5.update_traces(textposition='outside', textfont_size=11,
                           textfont_color=TEXT)
        fig5.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart(fig5), use_container_width=True)

# ── TAB 3: Risk Scoring ──
with tab3:
    st.markdown("<div class='chart-title' style='margin-bottom:4px'>User Risk Tiers</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-sub'>Channel IDs represent anonymised onboarding pathways (web, mobile, partner bundles). KKBox does not publish the mapping — but the churn rate difference between channels is real and significant.</div>", unsafe_allow_html=True)

    risk_df     = run_query(QUERY_RISK)
    tier_colors = {"High Risk":RED, "Medium Risk":AMBER, "Low Risk":GREEN}

    # Tier cards
    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1,r2,r3], risk_df.iterrows()):
        color = tier_colors.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{SURFACE}; border:1px solid {BORDER};
                        border-top:3px solid {color}; border-radius:10px;
                        padding:20px 22px; height:160px'>
              <div style='font-size:11px; font-weight:600; text-transform:uppercase;
                          letter-spacing:0.1em; color:{color}; margin-bottom:10px'>
                {row['risk_tier']}
              </div>
              <div style='font-family:Space Grotesk; font-size:32px; font-weight:700;
                          color:{TEXT}; line-height:1'>{int(row['users']):,}</div>
              <div style='font-size:12px; color:{MUTED}; margin-top:8px'>users</div>
              <div style='font-size:13px; color:{MUTED}; margin-top:10px'>
                Avg churn prob <b style='color:{color}'>{row['avg_prob']}%</b>
                &nbsp;·&nbsp; At risk <b style='color:{TEXT}'>TWD {row['rev_at_risk']:,.0f}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("<div class='chart-title'>Users by Risk Tier</div>", unsafe_allow_html=True)
        tiers    = risk_df['risk_tier'].tolist()
        counts   = risk_df['users'].tolist()
        clrs     = [tier_colors.get(t, MUTED) for t in tiers]
        fig6 = go.Figure(go.Bar(x=tiers, y=counts, marker_color=clrs,
                                text=[f"{v:,}" for v in counts],
                                textposition='outside',
                                textfont=dict(color=TEXT,size=13)))
        fig6.update_layout(yaxis_title="Users", showlegend=False)
        st.plotly_chart(chart(fig6, 320), use_container_width=True)

    with rc2:
        st.markdown("<div class='chart-title'>Revenue at Risk by Tier</div>", unsafe_allow_html=True)
        rev = risk_df['rev_at_risk'].tolist()
        fig7 = go.Figure(go.Bar(x=tiers, y=rev, marker_color=clrs,
                                text=[f"TWD {v:,.0f}" for v in rev],
                                textposition='outside',
                                textfont=dict(color=TEXT,size=11)))
        fig7.update_layout(yaxis_title="TWD", showlegend=False)
        st.plotly_chart(chart(fig7, 320), use_container_width=True)

    st.markdown(f"""
    <div class='insight-box'>
    <b>High Risk tier (19,869 users):</b> Average churn probability 95%+.
    These are users with auto-renew OFF, on long discounted plans, acquired via
    high-churn channels. Acting on this tier first maximises ROI per intervention dollar.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 4: Model Validation ──
with tab4:
    st.markdown(f"""
    <div style='background:{SURFACE}; border:1px solid {BORDER}; border-radius:10px;
                padding:20px 24px; margin-bottom:28px'>
      <div class='section-label'>Model Summary</div>
      <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:20px; margin-top:12px'>
        <div>
          <div style='font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:0.1em;font-weight:600'>Hold-out AUC</div>
          <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;color:{GREEN}'>0.9876</div>
        </div>
        <div>
          <div style='font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:0.1em;font-weight:600'>5-Fold CV Mean</div>
          <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;color:{GREEN}'>0.9875</div>
        </div>
        <div>
          <div style='font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:0.1em;font-weight:600'>CV Std Dev</div>
          <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;color:{TEXT}'>±0.0003</div>
        </div>
        <div>
          <div style='font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:0.1em;font-weight:600'>Optimal F1</div>
          <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;color:{TEXT}'>0.849</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2)

    with mv1:
        st.markdown("<div class='chart-title'>Logistic Regression Baseline vs XGBoost</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>LR establishes the linear ceiling. XGBoost's gain confirms non-linear subscription patterns justify the added complexity.</div>", unsafe_allow_html=True)
        st.image(str(ASSETS_PATH / "model_comparison.png"), use_column_width=True)

    with mv2:
        st.markdown("<div class='chart-title'>5-Fold Cross-Validation Stability</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>AUC 0.9875 mean, std 0.0003 across 5 folds. The score is stable — not a lucky train/test split.</div>", unsafe_allow_html=True)
        st.image(str(ASSETS_PATH / "cross_validation.png"), use_column_width=True)

    st.divider()

    mv3, mv4 = st.columns(2)

    with mv3:
        st.markdown("<div class='chart-title'>Threshold Optimisation</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Default 0.5 threshold gives F1 0.729. Optimal threshold 0.85 gives F1 0.849. For churn, missing a churner costs more than a false alarm.</div>", unsafe_allow_html=True)
        st.image(str(ASSETS_PATH / "threshold_analysis.png"), use_column_width=True)

    with mv4:
        st.markdown("<div class='chart-title'>SHAP Beeswarm — Direction per User</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Each dot = one user. Red = high feature value. Position right = pushes toward churn. Auto-renew OFF is the dominant signal across the entire test set.</div>", unsafe_allow_html=True)
        st.image(str(ASSETS_PATH / "shap_beeswarm.png"), use_column_width=True)

    st.divider()
    st.markdown("<div class='chart-title'>SHAP Dependence — Auto-Renew Deep Dive</div>", unsafe_allow_html=True)
    st.markdown("<div class='chart-sub'>Auto-renew OFF pushes predicted churn probability sharply upward. The most actionable single feature in the model.</div>", unsafe_allow_html=True)
    st.image(str(ASSETS_PATH / "shap_dependence_autorenew.png"), use_column_width=True)

# ── TAB 5: Recommendations ──
with tab5:
    roi = run_query(QUERY_ROI).iloc[0]

    # ROI hero
    st.markdown(f"""
    <div style='background:{SURFACE}; border:1px solid {BORDER};
                border-top:3px solid {GREEN}; border-radius:10px;
                padding:28px 32px; margin-bottom:28px'>
      <div class='section-label' style='color:{GREEN}'>Business Case · Intervention ROI</div>
      <div style='font-family:Space Grotesk; font-size:1.5rem; font-weight:700;
                  color:{TEXT}; margin:10px 0 8px; line-height:1.3'>
        A 10% auto-renew incentive targeted at {int(roi['n_high_risk']):,} high-risk users
        costs <span style='color:{AMBER}'>TWD {roi['cost_of_campaign']:,.0f}</span>
        and protects an estimated
        <span style='color:{GREEN}'>TWD {roi['revenue_saved']:,.0f}</span> in revenue.
      </div>
      <div style='font-size:13px; color:{MUTED}; line-height:1.6; max-width:680px'>
        Assumes 30% conversion rate (conservative) based on the observed 8× churn rate
        difference between auto-renew OFF (30.6%) and auto-renew ON (3.8%) users.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ROI metrics
    roi1, roi2, roi3, roi4 = st.columns(4)
    roi1.metric("High-Risk Users",    f"{int(roi['n_high_risk']):,}")
    roi2.metric("Revenue at Risk",    f"TWD {roi['revenue_at_risk']:,.0f}")
    roi3.metric("Campaign Cost",      f"TWD {roi['cost_of_campaign']:,.0f}")
    roi4.metric("Est. Revenue Saved", f"TWD {roi['revenue_saved']:,.0f}",
                delta=f"{roi['roi_ratio']}x ROI")

    st.divider()

    # Recommendation cards
    recs = [
        {
            "num": "01", "color": GREEN, "label": "HIGHEST IMPACT",
            "title": "Incentivise Auto-Renew",
            "finding": f"Auto-renew OFF users churn at 30.6% vs 3.8% for ON — an 8× gap. "
                       f"It is the single strongest churn signal in the model.",
            "action": f"Offer a permanent 10% discount for enabling auto-renew. "
                      f"Targeting {int(roi['n_high_risk']):,} high-risk users costs "
                      f"TWD {roi['cost_of_campaign']:,.0f} and protects "
                      f"TWD {roi['revenue_saved']:,.0f} — a {roi['roi_ratio']}x return.",
        },
        {
            "num": "02", "color": AMBER, "label": "REVENUE PROTECTION",
            "title": "Revisit Long-Plan Discount Strategy",
            "finding": "Churned users paid TWD 383 on average vs TWD 129 for retained users. "
                       "Heavily discounted long plans attract disloyal subscribers.",
            "action": "Stop using deep discounts on long plans as an acquisition lever. "
                      "Redirect that budget to loyalty rewards for existing monthly subscribers.",
        },
        {
            "num": "03", "color": ACCENT, "label": "ACQUISITION QUALITY",
            "title": "Cut Spend on High-Churn Channels",
            "finding": "Churn rate varies significantly by registration channel — the highest-churn "
           "channel is over 5× worse than the best. Acquisition channel is the third "
           "strongest churn predictor in SHAP.",
            "action": "Audit acquisition spend by channel. Reallocate budget from Channel 4 "
                      "to Channel 7 and other low-churn sources. Quality of user over volume.",
        },
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{SURFACE}; border:1px solid {BORDER};
                    border-left:4px solid {rec["color"]}; border-radius:0 10px 10px 0;
                    padding:22px 26px; margin-bottom:14px'>
          <div style='display:flex; align-items:baseline; gap:14px; margin-bottom:10px'>
            <span style='font-family:Space Grotesk; font-size:28px; font-weight:700;
                         color:{rec["color"]}; opacity:0.25'>{rec["num"]}</span>
            <div>
              <div style='font-size:10px; font-weight:600; text-transform:uppercase;
                          letter-spacing:0.1em; color:{rec["color"]}'>{rec["label"]}</div>
              <div style='font-size:16px; font-weight:600; color:{TEXT}'>{rec["title"]}</div>
            </div>
          </div>
          <div style='padding-left:44px'>
            <p style='font-size:13px;color:{MUTED};margin:0 0 6px;line-height:1.6'>
              <b style='color:{TEXT}'>Finding:</b> {rec["finding"]}
            </p>
            <p style='font-size:13px;color:{MUTED};margin:0;line-height:1.6'>
              <b style='color:{TEXT}'>Action:</b> {rec["action"]}
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <p style='font-size:12px; color:{DIM}; text-align:center'>
    WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
    XGBoost AUC 0.9876 · 5-fold CV 0.9875 ± 0.0003 &nbsp;·&nbsp;
    Built by Akanksha Nayak
    </p>
    """, unsafe_allow_html=True)