# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard — Redesigned v2
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
  .block-container {{ padding-top: 2rem !important; max-width: 1200px; }}

  /* ── Tabs ── */
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
      font-size: 15px;
      font-weight: 500;
      color: {MUTED};
      background: transparent;
      border-radius: 0;
      padding: 18px 32px;
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
  .stTabs [data-baseweb="tab"]:hover {{ color: {TEXT} !important; }}

  /* ── Metrics ── */
  div[data-testid="metric-container"] {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 10px;
      padding: 22px 24px;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.1em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {TEXT} !important;
      font-family: 'Space Grotesk', sans-serif !important;
      font-size: 28px !important;
      font-weight: 700 !important;
  }}

  hr {{ border-color: {BORDER} !important; margin: 28px 0 !important; }}

  .section-label {{
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: {MUTED};
      margin-bottom: 8px;
  }}
  .chart-title {{
      font-family: 'Space Grotesk', sans-serif;
      font-size: 17px;
      font-weight: 600;
      color: {TEXT};
      margin-bottom: 6px;
  }}
  .chart-sub {{
      font-size: 13px;
      color: {MUTED};
      margin-bottom: 16px;
      line-height: 1.6;
  }}
  .insight-box {{
      background: {SURFACE2};
      border-left: 3px solid {GREEN};
      border-radius: 0 8px 8px 0;
      padding: 16px 20px;
      margin: 16px 0;
      font-size: 14px;
      color: {TEXT};
      line-height: 1.7;
  }}
  .stat-pill {{
      display: inline-block;
      background: {SURFACE3};
      border: 1px solid {BORDER};
      border-radius: 20px;
      padding: 5px 16px;
      font-size: 13px;
      font-weight: 600;
      color: {TEXT};
      margin: 3px 3px;
  }}
  /* White-background image container for matplotlib charts */
  .img-card {{
      background: #FFFFFF;
      border-radius: 10px;
      padding: 16px;
      margin-top: 8px;
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
        font_size=13,
        title_font_family="Space Grotesk",
        title_font_size=15,
        margin=dict(t=24, b=24, l=10, r=10),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont_color=MUTED, tickfont_size=12),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont_color=MUTED, tickfont_size=12),
        legend=dict(bgcolor=SURFACE2, bordercolor=BORDER,
                    borderwidth=1, font_color=TEXT, font_size=13)
    )
    return fig

def img_card(path, caption=None):
    """Render a matplotlib image in a white card so it looks intentional."""
    st.markdown("<div class='img-card'>", unsafe_allow_html=True)
    st.image(str(path), use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='chart-sub' style='margin-top:8px'>{caption}</div>",
                    unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# QUERIES
# ════════════════════════════════════════════════════════
QUERY_OVERVIEW = """
    SELECT COUNT(*) AS total_users,
           ROUND(AVG(is_churn)*100,2) AS churn_rate_pct,
           ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) AS avg_rev_retained,
           ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) AS avg_rev_churned,
           ROUND(AVG(tenure_days),0) AS avg_tenure
    FROM users
"""
QUERY_AUTORENEW = """
    SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew ON' ELSE 'Auto-renew OFF' END AS status,
           COUNT(*) AS users, ROUND(AVG(is_churn)*100,2) AS churn_pct
    FROM users WHERE is_auto_renew IS NOT NULL
    GROUP BY is_auto_renew ORDER BY is_auto_renew DESC
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
# HERO
# ════════════════════════════════════════════════════════
overview = run_query(QUERY_OVERVIEW).iloc[0]

st.markdown(f"""
<div style='background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px;
            padding:40px 44px 36px; margin-bottom:28px'>
  <div class='section-label'>Portfolio Project · Music Streaming Analytics</div>
  <div style='font-family:Space Grotesk,sans-serif; font-size:2.2rem;
              font-weight:700; color:{TEXT}; line-height:1.25; margin:12px 0 16px'>
    🎵 KKBox Subscription Retention<br>&amp; Churn Analysis
  </div>
  <div style='font-size:14px; color:{MUTED}; max-width:620px;
              line-height:1.8; margin-bottom:24px'>
    Retention analysis across <b style='color:{TEXT}'>970,960 subscribers</b> on Asia's
    leading music streaming platform. Built to answer: who is churning,
    why are they leaving, and which users should we act on first?
  </div>
  <div style='margin-bottom:28px'>
    <span class='stat-pill'>Python</span>
    <span class='stat-pill'>SQL</span>
    <span class='stat-pill'>XGBoost</span>
    <span class='stat-pill'>SHAP</span>
    <span class='stat-pill'>Streamlit</span>
    <span class='stat-pill' style='border-color:{GREEN};color:{GREEN}'>AUC 0.9876</span>
    <span class='stat-pill' style='border-color:{ACCENT};color:{ACCENT}'>5-fold CV ±0.0003</span>
  </div>
  <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:20px;max-width:860px'>
    <div style='border-left:3px solid {GREEN};padding-left:16px'>
      <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.1em;font-weight:600;margin-bottom:4px'>Users Analysed</div>
      <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;
                  color:{TEXT}'>{int(overview['total_users']):,}</div>
    </div>
    <div style='border-left:3px solid {RED};padding-left:16px'>
      <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.1em;font-weight:600;margin-bottom:4px'>Churn Rate</div>
      <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;
                  color:{TEXT}'>{overview['churn_rate_pct']}%</div>
    </div>
    <div style='border-left:3px solid {AMBER};padding-left:16px'>
      <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.1em;font-weight:600;margin-bottom:4px'>Avg Rev · Retained</div>
      <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;
                  color:{TEXT}'>TWD {overview['avg_rev_retained']:,.0f}</div>
    </div>
    <div style='border-left:3px solid {ACCENT};padding-left:16px'>
      <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.1em;font-weight:600;margin-bottom:4px'>Avg Rev · Churned</div>
      <div style='font-family:Space Grotesk;font-size:24px;font-weight:700;
                  color:{RED}'>TWD {overview['avg_rev_churned']:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='background:{SURFACE2};border:1px solid {BORDER};
            border-left:4px solid {GREEN};border-radius:0 10px 10px 0;
            padding:18px 22px;margin-bottom:32px'>
  <div style='font-size:12px;font-weight:600;text-transform:uppercase;
              letter-spacing:0.1em;color:{GREEN};margin-bottom:6px'>Key Finding</div>
  <div style='font-size:15px;color:{TEXT};line-height:1.7'>
    Churned users paid <b style='color:{RED}'>3× more</b> than retained users
    (TWD {overview['avg_rev_churned']:,.0f} vs TWD {overview['avg_rev_retained']:,.0f}).
    Auto-renew OFF users churn at <b style='color:{RED}'>30.6%</b> vs
    <b style='color:{GREEN}'>3.8%</b> for auto-renew ON.
    <b>Churn here is a payments problem, not an engagement problem.</b>
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

# ── TAB 1 ──────────────────────────────────────────────
with tab1:
    cohort_df = run_query(QUERY_COHORT)
    avg_ret   = cohort_df['retention_rate'].mean()

    st.markdown("<div class='chart-title'>Monthly Cohort Retention Rates</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div class='chart-sub'>Each row = one month of signups. "
                f"Colour shows retention: red = below average ({avg_ret:.1f}%), "
                f"green = above. Split into two panels for readability.</div>",
                unsafe_allow_html=True)

    mid = len(cohort_df) // 2
    c1, c2 = st.columns(2)

    def cohort_fig(df_slice):
        f = px.bar(df_slice, x="retention_rate", y="cohort", orientation='h',
                   color="retention_rate",
                   color_continuous_scale=[[0,RED],[0.5,AMBER],[1,GREEN]],
                   text=df_slice['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                   labels={"retention_rate":"Retention (%)","cohort":""},
                   height=520)
        f.update_traces(textposition='outside', textfont_size=12, textfont_color=TEXT)
        f.update_layout(coloraxis_showscale=False, xaxis_range=[80,102],
                        yaxis={'categoryorder':'category ascending'})
        return chart(f)

    with c1:
        st.plotly_chart(cohort_fig(cohort_df.iloc[mid:]), use_container_width=True)
    with c2:
        st.plotly_chart(cohort_fig(cohort_df.iloc[:mid]), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Average Retention",  f"{avg_ret:.1f}%")
    m2.metric("Best Cohort",
              str(cohort_df.loc[cohort_df['retention_rate'].idxmax(),'cohort']),
              f"{cohort_df['retention_rate'].max():.1f}%")
    m3.metric("Cohorts Tracked", f"{len(cohort_df)}")

    st.markdown(f"""
    <div class='insight-box'>
    <b>What this tells us:</b> Retention is broadly stable at 85–94% across cohorts
    with no dramatic deterioration over time. The variation correlates with acquisition
    channel mix — cohorts with more high-churn channel signups retain worse.
    </div>""", unsafe_allow_html=True)

# ── TAB 2 ──────────────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div class='insight-box' style='border-color:{AMBER};margin-bottom:28px'>
    <b>Central finding:</b> Churned users listened just as much as retained users
    before leaving. Listening metrics (total seconds, completion rate, active days)
    barely register in the SHAP model. All dominant signals are payment-related.
    Product improvements won't fix this churn. Subscription management will.
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-title'>Churn Rate by Auto-Renew Status</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>The single strongest signal in the dataset — an 8× gap between ON and OFF.</div>",
                    unsafe_allow_html=True)
        auto_df = run_query(QUERY_AUTORENEW)
        f2 = px.bar(auto_df, x="status", y="churn_pct", color="status",
                    color_discrete_map={"Auto-renew ON":GREEN,"Auto-renew OFF":RED},
                    text=auto_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","status":""},
                    height=380)
        f2.update_traces(textposition='outside', textfont_size=16,
                         textfont_color=TEXT, width=0.4)
        f2.update_layout(showlegend=False, yaxis_range=[0,38])
        st.plotly_chart(chart(f2), use_container_width=True)

    with col2:
        st.markdown("<div class='chart-title'>Churn Rate by Plan Length</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Longer discounted plans attract lower-loyalty subscribers — counter-intuitive but consistent across the dataset.</div>",
                    unsafe_allow_html=True)
        plan_df = run_query(QUERY_PLAN)
        plan_df['label'] = plan_df['payment_plan_days'].apply(
            lambda x: {7:"7 days",30:"30 days",90:"3 months",
                       180:"6 months",365:"1 year"}.get(int(x), f"{int(x)}d"))
        f3 = px.bar(plan_df, x="label", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=plan_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","label":""},
                    height=380)
        f3.update_traces(textposition='outside', textfont_size=15,
                         textfont_color=TEXT)
        f3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart(f3), use_container_width=True)

    st.divider()

    col3, col4 = st.columns([3,2])

    with col3:
        st.markdown("<div class='chart-title'>What Drives Churn — SHAP Feature Importance</div>",
                    unsafe_allow_html=True)
        img_card(
            ASSETS_PATH / "shap_importance.png",
            "Payment method, plan price, and registration channel dominate. "
            "Listening metrics (total_secs, completion_rate) are near zero — "
            "confirming churn is not an engagement problem."
        )

    with col4:
        st.markdown("<div class='chart-title'>Churn by Acquisition Channel</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='chart-sub'>Channel IDs are anonymised onboarding pathways "
                    "(web, mobile, partner bundles). KKBox does not publish the mapping — "
                    "but the churn rate difference is real and significant.</div>",
                    unsafe_allow_html=True)
        reg_df = run_query(QUERY_REG)
        reg_df['channel'] = reg_df['registered_via'].apply(
            lambda x: f"Channel {int(x)}")
        f4 = px.bar(reg_df, x="channel", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=reg_df['churn_pct'].apply(lambda x: f"{x:.1f}%"),
                    labels={"churn_pct":"Churn (%)","channel":""},
                    height=420)
        f4.update_traces(textposition='outside', textfont_size=13, textfont_color=TEXT)
        f4.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart(f4), use_container_width=True)

# ── TAB 3 ──────────────────────────────────────────────
with tab3:
    st.markdown("<div class='chart-title' style='margin-bottom:6px'>User Risk Tiers</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='chart-sub'>Every user scored by churn probability. "
                "Three actionable tiers — high risk is the intervention priority.</div>",
                unsafe_allow_html=True)

    risk_df     = run_query(QUERY_RISK)
    tier_colors = {"High Risk":RED,"Medium Risk":AMBER,"Low Risk":GREEN}

    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1,r2,r3], risk_df.iterrows()):
        color = tier_colors.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{SURFACE};border:1px solid {BORDER};
                        border-top:3px solid {color};border-radius:10px;
                        padding:22px 24px;min-height:170px'>
              <div style='font-size:12px;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.1em;color:{color};margin-bottom:12px'>
                {row['risk_tier']}
              </div>
              <div style='font-family:Space Grotesk;font-size:34px;font-weight:700;
                          color:{TEXT};line-height:1'>{int(row['users']):,}</div>
              <div style='font-size:13px;color:{MUTED};margin-top:6px'>users</div>
              <div style='font-size:14px;color:{MUTED};margin-top:14px;line-height:1.7'>
                Avg churn prob <b style='color:{color}'>{row['avg_prob']}%</b><br>
                Revenue at risk <b style='color:{TEXT}'>TWD {row['rev_at_risk']:,.0f}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    rc1, rc2 = st.columns(2)
    tiers  = risk_df['risk_tier'].tolist()
    clrs   = [tier_colors.get(t,MUTED) for t in tiers]

    with rc1:
        st.markdown("<div class='chart-title'>Users by Risk Tier</div>",
                    unsafe_allow_html=True)
        counts = risk_df['users'].tolist()
        f5 = go.Figure(go.Bar(x=tiers, y=counts, marker_color=clrs,
                              text=[f"{v:,}" for v in counts],
                              textposition='outside',
                              textfont=dict(color=TEXT,size=14)))
        f5.update_layout(yaxis_title="Users", showlegend=False)
        st.plotly_chart(chart(f5, 360), use_container_width=True)

    with rc2:
        st.markdown("<div class='chart-title'>Revenue at Risk by Tier</div>",
                    unsafe_allow_html=True)
        rev = risk_df['rev_at_risk'].tolist()
        f6 = go.Figure(go.Bar(x=tiers, y=rev, marker_color=clrs,
                              text=[f"TWD {v:,.0f}" for v in rev],
                              textposition='outside',
                              textfont=dict(color=TEXT,size=13)))
        f6.update_layout(yaxis_title="TWD", showlegend=False)
        st.plotly_chart(chart(f6, 360), use_container_width=True)

    st.markdown(f"""
    <div class='insight-box'>
    <b>High Risk tier (19,869 users):</b> Average churn probability 95%+.
    These are users with auto-renew OFF, on long discounted plans, acquired
    via high-churn channels. Acting on this tier first maximises ROI
    per intervention dollar — modelled at a 2.8x return.
    </div>""", unsafe_allow_html=True)

# ── TAB 4 ──────────────────────────────────────────────
with tab4:
    st.markdown(f"""
    <div style='background:{SURFACE};border:1px solid {BORDER};border-radius:10px;
                padding:24px 28px;margin-bottom:28px'>
      <div class='section-label'>Model Summary</div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-top:14px'>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:600;margin-bottom:6px'>Hold-out AUC</div>
          <div style='font-family:Space Grotesk;font-size:28px;font-weight:700;
                      color:{GREEN}'>0.9876</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:600;margin-bottom:6px'>5-Fold CV Mean</div>
          <div style='font-family:Space Grotesk;font-size:28px;font-weight:700;
                      color:{GREEN}'>0.9875</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:600;margin-bottom:6px'>CV Std Dev</div>
          <div style='font-family:Space Grotesk;font-size:28px;font-weight:700;
                      color:{TEXT}'>±0.0003</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:600;margin-bottom:6px'>Optimal F1</div>
          <div style='font-family:Space Grotesk;font-size:28px;font-weight:700;
                      color:{TEXT}'>0.849</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2)

    with mv1:
        st.markdown("<div class='chart-title'>Baseline vs XGBoost</div>",
                    unsafe_allow_html=True)
        img_card(
            ASSETS_PATH / "model_comparison.png",
            "LR baseline AUC 0.9028. XGBoost 0.9876. "
            "The gap confirms non-linear subscription patterns "
            "justify the added model complexity."
        )

    with mv2:
        st.markdown("<div class='chart-title'>5-Fold Cross-Validation Stability</div>",
                    unsafe_allow_html=True)
        img_card(
            ASSETS_PATH / "cross_validation.png",
            "Mean AUC 0.9875, std 0.0003 across 5 folds. "
            "The score is stable — not a lucky train/test split."
        )

    st.divider()

    mv3, mv4 = st.columns(2)

    with mv3:
        st.markdown("<div class='chart-title'>Threshold Optimisation</div>",
                    unsafe_allow_html=True)
        img_card(
            ASSETS_PATH / "threshold_analysis.png",
            "Default 0.5 threshold: F1 0.729. "
            "Optimal 0.85 threshold: F1 0.849. "
            "For churn, a missed churner costs more than a false alarm."
        )

    with mv4:
        st.markdown("<div class='chart-title'>SHAP Beeswarm — Direction per User</div>",
                    unsafe_allow_html=True)
        img_card(
            ASSETS_PATH / "shap_beeswarm.png",
            "Each dot = one user. Red = high feature value. "
            "Right = pushes toward churn. "
            "Auto-renew OFF is the dominant signal across the test set."
        )

    st.divider()
    st.markdown("<div class='chart-title'>SHAP Dependence — Auto-Renew Deep Dive</div>",
                unsafe_allow_html=True)
    img_card(
        ASSETS_PATH / "shap_dependence_autorenew.png",
        "Auto-renew OFF (value = 0, left column) pushes SHAP value sharply upward — "
        "increasing predicted churn probability. The most actionable single feature in the model."
    )

# ── TAB 5 ──────────────────────────────────────────────
with tab5:
    roi = run_query(QUERY_ROI).iloc[0]

    st.markdown(f"""
    <div style='background:{SURFACE};border:1px solid {BORDER};
                border-top:3px solid {GREEN};border-radius:10px;
                padding:30px 34px;margin-bottom:28px'>
      <div class='section-label' style='color:{GREEN}'>Business Case · Intervention ROI</div>
      <div style='font-family:Space Grotesk;font-size:1.6rem;font-weight:700;
                  color:{TEXT};margin:12px 0 10px;line-height:1.35'>
        A 10% auto-renew incentive targeted at
        <span style='color:{GREEN}'>{int(roi['n_high_risk']):,} high-risk users</span>
        costs <span style='color:{AMBER}'>TWD {roi['cost_of_campaign']:,.0f}</span>
        and protects an estimated
        <span style='color:{GREEN}'>TWD {roi['revenue_saved']:,.0f}</span> in revenue.
      </div>
      <div style='font-size:14px;color:{MUTED};line-height:1.7;max-width:700px'>
        Assumes 30% conversion rate (conservative) based on the 8× churn rate difference
        between auto-renew OFF (30.6%) and auto-renew ON (3.8%) users.
      </div>
    </div>
    """, unsafe_allow_html=True)

    roi1, roi2, roi3, roi4 = st.columns(4)
    roi1.metric("High-Risk Users",    f"{int(roi['n_high_risk']):,}")
    roi2.metric("Revenue at Risk",    f"TWD {roi['revenue_at_risk']:,.0f}")
    roi3.metric("Campaign Cost",      f"TWD {roi['cost_of_campaign']:,.0f}")
    roi4.metric("Est. Revenue Saved", f"TWD {roi['revenue_saved']:,.0f}",
                delta=f"{roi['roi_ratio']}x ROI")

    st.divider()

    recs = [
        {
            "num":"01","color":GREEN,"label":"HIGHEST IMPACT",
            "title":"Incentivise Auto-Renew",
            "finding":f"Auto-renew OFF users churn at 30.6% vs 3.8% for ON — an 8× gap. "
                      f"It is the single strongest churn signal in the model.",
            "action": f"Offer a permanent 10% discount for enabling auto-renew. "
                      f"Targeting {int(roi['n_high_risk']):,} high-risk users costs "
                      f"TWD {roi['cost_of_campaign']:,.0f} and protects "
                      f"TWD {roi['revenue_saved']:,.0f} — a {roi['roi_ratio']}x return.",
        },
        {
            "num":"02","color":AMBER,"label":"REVENUE PROTECTION",
            "title":"Revisit Long-Plan Discount Strategy",
            "finding":"Churned users paid TWD 383 on average vs TWD 129 for retained users. "
                      "Heavily discounted long plans attract disloyal subscribers.",
            "action": "Stop using deep discounts on long plans as an acquisition lever. "
                      "Redirect budget to loyalty rewards for existing monthly subscribers.",
        },
        {
            "num":"03","color":ACCENT,"label":"ACQUISITION QUALITY",
            "title":"Cut Spend on High-Churn Channels",
            "finding":"Churn rate varies significantly by registration channel — the highest-churn "
                      "channel is over 5× worse than the best. Acquisition channel is the third "
                      "strongest churn predictor in SHAP.",
            "action": "Audit acquisition spend by channel. Reallocate from high-churn "
                      "channels to low-churn sources. Quality of user over volume.",
        },
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{SURFACE};border:1px solid {BORDER};
                    border-left:4px solid {rec["color"]};border-radius:0 10px 10px 0;
                    padding:24px 28px;margin-bottom:14px'>
          <div style='display:flex;align-items:baseline;gap:16px;margin-bottom:12px'>
            <span style='font-family:Space Grotesk;font-size:30px;font-weight:700;
                         color:{rec["color"]};opacity:0.25'>{rec["num"]}</span>
            <div>
              <div style='font-size:11px;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.1em;color:{rec["color"]}'>{rec["label"]}</div>
              <div style='font-size:17px;font-weight:600;color:{TEXT}'>{rec["title"]}</div>
            </div>
          </div>
          <div style='padding-left:50px'>
            <p style='font-size:14px;color:{MUTED};margin:0 0 8px;line-height:1.7'>
              <b style='color:{TEXT}'>Finding:</b> {rec["finding"]}
            </p>
            <p style='font-size:14px;color:{MUTED};margin:0;line-height:1.7'>
              <b style='color:{TEXT}'>Action:</b> {rec["action"]}
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <p style='font-size:13px;color:{DIM};text-align:center'>
    WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
    XGBoost AUC 0.9876 · 5-fold CV 0.9875 ±0.0003 &nbsp;·&nbsp;
    Built by Akanksha Nayak
    </p>
    """, unsafe_allow_html=True)