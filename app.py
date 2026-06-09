# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard — Dark Analytics Theme
# Author: Akanksha Nayak
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ──
st.set_page_config(
    page_title="KKBox Retention Analysis",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Design tokens ──
BG          = "#0D0D0D"
SURFACE     = "#161616"
SURFACE2    = "#1F1F1F"
BORDER      = "#2A2A2A"
GREEN       = "#00C48C"
RED         = "#FF4D4D"
AMBER       = "#FFB547"
TEXT        = "#F0F0F0"
MUTED       = "#888888"
ACCENT      = "#7B61FF"

# ── Global CSS ──
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Inter', sans-serif;
      background-color: {BG};
      color: {TEXT};
  }}
  .stApp {{ background-color: {BG}; }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 4px;
      background: {SURFACE};
      padding: 6px;
      border-radius: 12px;
      border: 1px solid {BORDER};
  }}
  .stTabs [data-baseweb="tab"] {{
      font-family: 'Inter', sans-serif;
      font-size: 13px;
      font-weight: 500;
      color: {MUTED};
      background: transparent;
      border-radius: 8px;
      padding: 8px 18px;
      border: none;
  }}
  .stTabs [aria-selected="true"] {{
      background: {SURFACE2} !important;
      color: {TEXT} !important;
      border: 1px solid {BORDER} !important;
  }}

  /* Metrics */
  div[data-testid="metric-container"] {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 20px 24px;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important;
      font-size: 12px !important;
      font-weight: 500 !important;
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {TEXT} !important;
      font-family: 'Space Grotesk', sans-serif !important;
      font-size: 28px !important;
      font-weight: 700 !important;
  }}

  /* Divider */
  hr {{ border-color: {BORDER} !important; }}

  /* Headers */
  h1, h2, h3 {{
      font-family: 'Space Grotesk', sans-serif !important;
      color: {TEXT} !important;
  }}
  h1 {{ font-size: 2rem !important; font-weight: 700 !important; }}
  h3 {{ color: {GREEN} !important; }}

  /* Caption */
  .caption-text {{
      font-size: 12px;
      color: {MUTED};
      font-style: italic;
      margin-top: -8px;
      margin-bottom: 12px;
  }}

  /* Insight cards */
  .insight-card {{
      background: {SURFACE};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 16px;
  }}
  .insight-card h3 {{
      margin: 0 0 8px 0;
      font-size: 15px;
      color: {TEXT} !important;
  }}
  .insight-card p {{
      margin: 4px 0;
      font-size: 13px;
      color: {MUTED};
      line-height: 1.6;
  }}
  .insight-card .label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
  }}
</style>
""", unsafe_allow_html=True)

# ── Paths ──
DB_PATH     = Path("data/kkbox.db")
ASSETS_PATH = Path("assets")

# ── DB helpers ──
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

def styled_chart(fig):
    fig.update_layout(
        plot_bgcolor=SURFACE2,
        paper_bgcolor=SURFACE,
        font_color=TEXT,
        font_family="Inter",
        title_font_family="Space Grotesk",
        title_font_size=14,
        margin=dict(t=40, b=20, l=10, r=10),
        xaxis=dict(
            gridcolor=BORDER,
            linecolor=BORDER,
            tickcolor=BORDER,
            tickfont_color=MUTED
        ),
        yaxis=dict(
            gridcolor=BORDER,
            linecolor=BORDER,
            tickcolor=BORDER,
            tickfont_color=MUTED
        ),
        legend=dict(
            bgcolor=SURFACE2,
            bordercolor=BORDER,
            borderwidth=1,
            font_color=TEXT
        )
    )
    return fig

# ════════════════════════════════════════════════════════════
# SQL QUERIES
# ════════════════════════════════════════════════════════════

QUERY_OVERVIEW = """
    SELECT
        COUNT(*)                                    AS total_users,
        ROUND(AVG(is_churn) * 100, 2)              AS churn_rate_pct,
        ROUND(AVG(actual_amount_paid), 2)          AS avg_revenue,
        ROUND(AVG(tenure_days), 0)                 AS avg_tenure_days,
        ROUND(AVG(CASE WHEN is_churn = 0
              THEN actual_amount_paid END), 2)     AS avg_rev_retained,
        ROUND(AVG(CASE WHEN is_churn = 1
              THEN actual_amount_paid END), 2)     AS avg_rev_churned
    FROM users
"""

QUERY_AUTORENEW = """
    SELECT
        CASE WHEN is_auto_renew = 1
             THEN 'Auto-renew ON'
             ELSE 'Auto-renew OFF' END             AS auto_renew_status,
        COUNT(*)                                   AS user_count,
        ROUND(AVG(is_churn) * 100, 2)             AS churn_rate_pct
    FROM users
    WHERE is_auto_renew IS NOT NULL
    GROUP BY is_auto_renew
    ORDER BY is_auto_renew DESC
"""

QUERY_PLAN_CHURN = """
    SELECT
        payment_plan_days,
        COUNT(*)                                   AS user_count,
        ROUND(AVG(is_churn) * 100, 2)             AS churn_rate_pct,
        ROUND(AVG(actual_amount_paid), 2)         AS avg_amount_paid
    FROM users
    WHERE payment_plan_days IS NOT NULL
      AND payment_plan_days IN (7, 30, 90, 180, 365)
    GROUP BY payment_plan_days
    ORDER BY payment_plan_days
"""

QUERY_RISK_SUMMARY = """
    SELECT
        risk_tier,
        COUNT(*)                                   AS user_count,
        ROUND(AVG(churn_probability) * 100, 1)    AS avg_churn_prob_pct,
        ROUND(AVG(actual_churn) * 100, 1)         AS actual_churn_rate_pct,
        ROUND(AVG(plan_list_price), 2)            AS avg_plan_price,
        ROUND(SUM(churn_probability *
              plan_list_price), 0)                AS revenue_at_risk
    FROM risk_scores
    GROUP BY risk_tier
    ORDER BY avg_churn_prob_pct DESC
"""

QUERY_COHORT = """
    SELECT cohort, cohort_size, retained, retention_rate
    FROM cohort_retention
    WHERE cohort >= '2015-01'
    ORDER BY cohort
"""

QUERY_REGISTRATION = """
    SELECT
        registered_via,
        COUNT(*)                                   AS user_count,
        ROUND(AVG(is_churn) * 100, 2)             AS churn_rate_pct
    FROM users
    WHERE registered_via IS NOT NULL
    GROUP BY registered_via
    ORDER BY churn_rate_pct DESC
"""

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.markdown(f"""
<div style='padding: 2rem 0 1rem 0;'>
  <div style='font-size:11px; font-weight:600; letter-spacing:0.12em;
              text-transform:uppercase; color:{ACCENT}; margin-bottom:8px;'>
    PORTFOLIO PROJECT · MUSIC STREAMING ANALYTICS
  </div>
  <h1 style='font-family: Space Grotesk, sans-serif;
             font-size: 2.4rem; font-weight:700;
             color:{TEXT}; margin:0 0 12px 0; line-height:1.2'>
    🎵 KKBox Subscription Retention<br>& Churn Analysis
  </h1>
  <p style='color:{MUTED}; font-size:14px; max-width:680px; line-height:1.7; margin:0'>
    A full-stack retention analysis of <b style='color:{TEXT}'>970,000+ subscribers</b>
    on Asia's leading music streaming platform — covering cohort retention curves,
    behavioural churn signals, revenue impact quantification, and ML-powered
    risk scoring.<br>
    <span style='color:{ACCENT}'>SQL · Python · XGBoost · SHAP · Streamlit</span>
    &nbsp;·&nbsp;
    <span style='color:{GREEN}'>Model AUC: 0.947</span>
  </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── KPI row ──
overview = run_query(QUERY_OVERVIEW).iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Users Analysed",   f"{int(overview['total_users']):,}")
k2.metric("Overall Churn Rate",     f"{overview['churn_rate_pct']}%")
k3.metric("Avg Revenue — Retained", f"TWD {overview['avg_rev_retained']:,.0f}")
k4.metric("Avg Revenue — Churned",
          f"TWD {overview['avg_rev_churned']:,.0f}",
          delta=f"{overview['avg_rev_churned'] - overview['avg_rev_retained']:+.0f} vs retained",
          delta_color="inverse")

st.divider()

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Cohort Retention",
    "🔍  Churn Patterns",
    "🤖  Risk Scoring",
    "💡  Recommendations"
])

# ── TAB 1 ──
with tab1:
    st.markdown(f"<div class='caption-text'>Each bar = one monthly user cohort · Colour scale: red = lower retention → green = higher retention</div>",
                unsafe_allow_html=True)

    cohort_df = run_query(QUERY_COHORT)
    fig = px.bar(
        cohort_df, x="retention_rate", y="cohort",
        orientation='h',
        color="retention_rate",
        color_continuous_scale=[[0, RED], [0.5, AMBER], [1, GREEN]],
        text=cohort_df['retention_rate'].apply(lambda x: f"{x:.1f}%"),
        labels={"retention_rate": "Retention Rate (%)", "cohort": ""},
        height=720
    )
    fig.update_traces(textposition='outside', textfont_size=11)
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_range=[80, 102],
        yaxis={'categoryorder': 'category ascending'},
        title=""
    )
    st.plotly_chart(styled_chart(fig), use_container_width=True)

    m1, m2 = st.columns(2)
    m1.metric("Avg Retention Rate",  f"{cohort_df['retention_rate'].mean():.1f}%")
    m2.metric("Cohorts Analysed",    f"{len(cohort_df)}")

# ── TAB 2 ──
with tab2:
    st.markdown(f"<div class='caption-text'>Churn at KKBox is a payments problem, not an engagement problem — users listen just as much before they leave.</div>",
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"<p style='font-size:13px;font-weight:600;color:{TEXT}'>Churn Rate by Auto-Renew Status</p>",
                    unsafe_allow_html=True)
        auto_df = run_query(QUERY_AUTORENEW)
        fig2 = px.bar(
            auto_df, x="auto_renew_status", y="churn_rate_pct",
            color="auto_renew_status",
            color_discrete_map={"Auto-renew ON": GREEN, "Auto-renew OFF": RED},
            text=auto_df['churn_rate_pct'].apply(lambda x: f"{x}%"),
            labels={"churn_rate_pct": "Churn Rate (%)", "auto_renew_status": ""},
            height=360
        )
        fig2.update_traces(textposition='outside', textfont_size=13,
                           textfont_color=TEXT)
        fig2.update_layout(showlegend=False, yaxis_range=[0, 40])
        st.plotly_chart(styled_chart(fig2), use_container_width=True)
        st.markdown(f"<div class='caption-text'>8× difference in churn rate — the single strongest signal in the dataset.</div>",
                    unsafe_allow_html=True)

    with c2:
        st.markdown(f"<p style='font-size:13px;font-weight:600;color:{TEXT}'>Churn Rate by Plan Length</p>",
                    unsafe_allow_html=True)
        plan_df = run_query(QUERY_PLAN_CHURN)
        plan_df['plan_label'] = plan_df['payment_plan_days'].apply(
            lambda x: f"{int(x)}d")
        fig3 = px.bar(
            plan_df, x="plan_label", y="churn_rate_pct",
            color="churn_rate_pct",
            color_continuous_scale=[[0, GREEN], [0.5, AMBER], [1, RED]],
            text=plan_df['churn_rate_pct'].apply(lambda x: f"{x}%"),
            labels={"churn_rate_pct": "Churn Rate (%)", "plan_label": "Plan Length"},
            height=360
        )
        fig3.update_traces(textposition='outside', textfont_size=13,
                           textfont_color=TEXT)
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(styled_chart(fig3), use_container_width=True)
        st.markdown(f"<div class='caption-text'>Longer discounted plans attract lower-loyalty users — counter-intuitive but consistent.</div>",
                    unsafe_allow_html=True)

    st.divider()
    st.markdown(f"<p style='font-size:13px;font-weight:600;color:{TEXT}'>What the Model Learned — SHAP Feature Importance</p>",
                unsafe_allow_html=True)
    st.markdown(f"<div class='caption-text'>Payment behaviour dominates. Listening behaviour barely registers. Churn is a subscription management problem.</div>",
                unsafe_allow_html=True)
    st.image(str(ASSETS_PATH / "shap_importance.png"), width=700)

    st.divider()
    st.markdown(f"<p style='font-size:13px;font-weight:600;color:{TEXT}'>Churn Rate by Registration Channel</p>",
                unsafe_allow_html=True)
    reg_df = run_query(QUERY_REGISTRATION)
    fig4 = px.bar(
        reg_df, x=reg_df['registered_via'].astype(str), y="churn_rate_pct",
        color="churn_rate_pct",
        color_continuous_scale=[[0, GREEN], [0.5, AMBER], [1, RED]],
        text=reg_df['churn_rate_pct'].apply(lambda x: f"{x}%"),
        labels={"churn_rate_pct": "Churn Rate (%)", "x": "Channel ID"},
        height=350
    )
    fig4.update_traces(textposition='outside', textfont_size=12,
                       textfont_color=TEXT)
    fig4.update_layout(coloraxis_showscale=False)
    st.plotly_chart(styled_chart(fig4), use_container_width=True)
    st.markdown(f"<div class='caption-text'>Certain acquisition channels produce 2–3× higher churn — targeting strategy needs revision.</div>",
                unsafe_allow_html=True)

# ── TAB 3 ──
with tab3:
    st.markdown(f"<div class='caption-text'>XGBoost model scores every user by churn probability. Three tiers guide where to focus retention spend.</div>",
                unsafe_allow_html=True)

    risk_df = run_query(QUERY_RISK_SUMMARY)
    tier_colors = {"High Risk": RED, "Medium Risk": AMBER, "Low Risk": GREEN}

    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1, r2, r3], risk_df.iterrows()):
        color = tier_colors.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{SURFACE}; border:1px solid {BORDER};
                        border-top: 3px solid {color};
                        border-radius:12px; padding:20px 24px;'>
              <div style='font-size:11px; font-weight:600; letter-spacing:0.1em;
                          text-transform:uppercase; color:{color}; margin-bottom:8px;'>
                {row['risk_tier']}
              </div>
              <div style='font-size:28px; font-weight:700; font-family:Space Grotesk;
                          color:{TEXT}; margin-bottom:12px;'>
                {int(row['user_count']):,}
                <span style='font-size:13px; font-weight:400;
                             color:{MUTED}'>users</span>
              </div>
              <div style='font-size:13px; color:{MUTED}; line-height:1.8'>
                Avg churn prob: <b style='color:{color}'>{row['avg_churn_prob_pct']}%</b><br>
                Revenue at risk: <b style='color:{TEXT}'>TWD {row['revenue_at_risk']:,.0f}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    rc1, rc2 = st.columns(2)
    with rc1:
        tiers    = risk_df['risk_tier'].tolist()
        counts   = risk_df['user_count'].tolist()
        colors_l = [tier_colors.get(t, MUTED) for t in tiers]
        fig5 = go.Figure(go.Bar(
            x=tiers, y=counts,
            marker_color=colors_l,
            text=[f"{v:,}" for v in counts],
            textposition='outside',
            textfont=dict(color=TEXT, size=12)
        ))
        fig5.update_layout(title="Users by Risk Tier",
                           yaxis_title="Users", showlegend=False)
        st.plotly_chart(styled_chart(fig5), use_container_width=True)

    with rc2:
        rev_risk = risk_df['revenue_at_risk'].tolist()
        fig6 = go.Figure(go.Bar(
            x=tiers, y=rev_risk,
            marker_color=colors_l,
            text=[f"TWD {v:,.0f}" for v in rev_risk],
            textposition='outside',
            textfont=dict(color=TEXT, size=11)
        ))
        fig6.update_layout(title="Revenue at Risk by Tier",
                           yaxis_title="TWD", showlegend=False)
        st.plotly_chart(styled_chart(fig6), use_container_width=True)

# ── TAB 4 ──
with tab4:
    st.markdown(f"<div class='caption-text'>Three prioritised interventions — ranked by revenue impact and feasibility.</div>",
                unsafe_allow_html=True)

    recs = [
        {
            "num": "01",
            "color": GREEN,
            "label": "HIGHEST IMPACT",
            "title": "🔄 Incentivise Auto-Renew — Don't Force It",
            "finding": "Auto-renew OFF users churn at 30.6% vs 3.8% for auto-renew ON — an 8× gap.",
            "action": "Offer a permanent 10% discount for enabling auto-renew. Cost of discount is far lower than cost of reacquisition. Target the 17,769 high-risk users first.",
        },
        {
            "num": "02",
            "color": AMBER,
            "label": "REVENUE PROTECTION",
            "title": "💰 Revisit Long-Plan Discount Strategy",
            "finding": "Users on longer discounted plans churn more. Churned users paid TWD 383 on average vs TWD 129 for retained users.",
            "action": "Stop using heavy discounts on long plans as an acquisition tool — you're buying disloyal customers. Redirect budget to loyalty rewards for existing monthly subscribers.",
        },
        {
            "num": "03",
            "color": ACCENT,
            "label": "ACQUISITION QUALITY",
            "title": "📱 Double Down on High-Retention Channels",
            "finding": "Churn rate varies significantly by registration channel. Certain channels produce users with 2–3× higher churn rates.",
            "action": "Audit acquisition spend by channel. Cut budget from high-churn channels, reallocate to channels producing loyal users. Quality over volume.",
        },
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{SURFACE}; border:1px solid {BORDER};
                    border-left: 4px solid {rec["color"]};
                    border-radius:12px; padding:24px 28px; margin-bottom:16px;'>
          <div style='display:flex; align-items:center; gap:12px; margin-bottom:10px;'>
            <span style='font-size:32px; font-weight:700; font-family:Space Grotesk;
                         color:{rec["color"]}; opacity:0.3'>{rec["num"]}</span>
            <div>
              <div style='font-size:10px; font-weight:600; letter-spacing:0.1em;
                          text-transform:uppercase; color:{rec["color"]};
                          margin-bottom:2px'>{rec["label"]}</div>
              <div style='font-size:16px; font-weight:600;
                          color:{TEXT}'>{rec["title"]}</div>
            </div>
          </div>
          <div style='margin-left:52px'>
            <p style='font-size:13px; color:{MUTED}; margin:0 0 6px 0;
                      line-height:1.6'>
              <b style='color:{TEXT}'>Finding:</b> {rec["finding"]}
            </p>
            <p style='font-size:13px; color:{MUTED}; margin:0;
                      line-height:1.6'>
              <b style='color:{TEXT}'>Action:</b> {rec["action"]}
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <p style='font-size:12px; color:{MUTED}; text-align:center'>
    Analysis based on WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
    Model AUC: 0.947 &nbsp;·&nbsp;
    Built by Akanksha Nayak
    </p>
    """, unsafe_allow_html=True)