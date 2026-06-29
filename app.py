# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard v3 — Data Journalism Style
# Author: Akanksha Nayak
# ============================================================
from pathlib import Path
import gdown

DB_PATH = Path("data/kkbox.db")
if not DB_PATH.exists():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdown.download(
        "https://drive.google.com/uc?id=1RExff-WGtouE_yMtAWcQR0_hPvYjIpw8",
        str(DB_PATH), quiet=False
    )

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="KKBox Churn Analysis",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Tokens ──
BG      = "#0C0C0C"
CARD    = "#141414"
CARD2   = "#1C1C1C"
BORDER  = "#2A2A2A"
GREEN   = "#00C48C"
RED     = "#FF4D4D"
AMBER   = "#FFB547"
TEXT    = "#EFEFEF"
SUB     = "#AAAAAA"
MUTED   = "#666666"
ACCENT  = "#7B61FF"
WHITE   = "#FFFFFF"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

  html, body, [class*="css"] {{
      font-family: 'DM Sans', sans-serif !important;
      background-color: {BG};
      color: {TEXT};
  }}
  .stApp {{ background-color: {BG}; }}
  .block-container {{ padding-top: 2rem !important; max-width: 1280px; }}

  /* ── Big underline tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 0;
      background: transparent;
      padding: 0;
      border-bottom: 1px solid {BORDER};
      margin-bottom: 36px;
  }}
  .stTabs [data-baseweb="tab"] {{
      font-family: 'DM Sans', sans-serif !important;
      font-size: 15px;
      font-weight: 500;
      color: {MUTED};
      background: transparent;
      padding: 16px 30px;
      border: none;
      border-bottom: 3px solid transparent;
      margin-bottom: -1px;
  }}
  .stTabs [aria-selected="true"] {{
      color: {WHITE} !important;
      border-bottom: 3px solid {GREEN} !important;
      font-weight: 600 !important;
      background: transparent !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{ color: {TEXT} !important; }}

  /* ── Metrics ── */
  div[data-testid="metric-container"] {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 24px 26px;
  }}
  div[data-testid="metric-container"] label {{
      color: {SUB} !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.1em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {WHITE} !important;
      font-family: 'DM Sans', sans-serif !important;
      font-size: 30px !important;
      font-weight: 700 !important;
  }}
  div[data-testid="stMetricDelta"] {{
      font-size: 13px !important;
  }}

  hr {{ border-color: {BORDER} !important; margin: 32px 0 !important; }}

  /* ── Typography helpers ── */
  .eyebrow {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: {MUTED};
      margin-bottom: 8px;
  }}
  .headline {{
      font-family: 'DM Serif Display', serif;
      font-size: 2.4rem;
      font-weight: 400;
      color: {WHITE};
      line-height: 1.2;
      margin-bottom: 16px;
  }}
  .subhead {{
      font-size: 15px;
      color: {SUB};
      line-height: 1.8;
      max-width: 640px;
  }}
  .chart-hed {{
      font-family: 'DM Sans', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: {WHITE};
      margin-bottom: 4px;
      line-height: 1.3;
  }}
  .chart-dek {{
      font-size: 13px;
      color: {SUB};
      line-height: 1.6;
      margin-bottom: 14px;
  }}
  .finding {{
      background: {CARD2};
      border-left: 3px solid {GREEN};
      border-radius: 0 10px 10px 0;
      padding: 18px 22px;
      margin: 20px 0;
      font-size: 15px;
      color: {TEXT};
      line-height: 1.8;
  }}
  .finding-amber {{ border-left-color: {AMBER}; }}
  .finding-red   {{ border-left-color: {RED}; }}
  .pill {{
      display: inline-block;
      background: {CARD2};
      border: 1px solid {BORDER};
      border-radius: 20px;
      padding: 5px 16px;
      font-size: 13px;
      font-weight: 600;
      color: {TEXT};
      margin: 3px 2px;
  }}
  /* White card for matplotlib images */
  .img-wrap {{
      background: #F7F7F7;
      border-radius: 12px;
      padding: 20px 20px 12px;
      margin-bottom: 8px;
  }}
  .stat-row {{
      display: grid;
      grid-template-columns: repeat(4,1fr);
      gap: 20px;
      margin-top: 28px;
  }}
  .stat-item {{
      border-left: 3px solid;
      padding-left: 16px;
  }}
  .stat-label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: {MUTED};
      margin-bottom: 4px;
  }}
  .stat-value {{
      font-family: 'DM Sans', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: {WHITE};
  }}
</style>
""", unsafe_allow_html=True)

DB_PATH     = Path("data/kkbox.db")
ASSETS_PATH = Path("assets")

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def q(sql):
    return pd.read_sql(sql, get_conn())

def C(fig, h=None):
    """Apply dark theme to plotly chart."""
    updates = dict(
        plot_bgcolor=CARD2, paper_bgcolor=CARD,
        font=dict(color=TEXT, family="DM Sans", size=13),
        title_font=dict(family="DM Sans", size=15),
        margin=dict(t=16, b=16, l=8, r=8),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=SUB, size=12)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=SUB, size=12)),
        legend=dict(bgcolor=CARD2, bordercolor=BORDER,
                    font=dict(color=TEXT, size=13))
    )
    if h:
        updates['height'] = h
    fig.update_layout(**updates)
    return fig

def img(path, caption=""):
    st.markdown("<div class='img-wrap'>", unsafe_allow_html=True)
    st.image(str(path), use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='chart-dek' style='margin-top:6px'>{caption}</div>",
                    unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════
ov       = q("SELECT COUNT(*) total, ROUND(AVG(is_churn)*100,2) churn, ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) rev_ret, ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) rev_ch FROM users").iloc[0]
cohort   = q("SELECT cohort, cohort_size, retained, retention_rate FROM cohort_retention WHERE cohort>='2015-01' ORDER BY cohort")
auto_df  = q("SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew ON' ELSE 'Auto-renew OFF' END status, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE is_auto_renew IS NOT NULL GROUP BY is_auto_renew ORDER BY is_auto_renew DESC")
plan_df  = q("SELECT payment_plan_days, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE payment_plan_days IN (7,30,90,180,365) GROUP BY payment_plan_days ORDER BY payment_plan_days")
reg_df   = q("SELECT registered_via, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE registered_via IS NOT NULL GROUP BY registered_via ORDER BY churn_pct DESC")
risk_df  = q("SELECT risk_tier, COUNT(*) users, ROUND(AVG(churn_probability)*100,1) avg_prob, ROUND(SUM(churn_probability*plan_list_price),0) rev_at_risk FROM risk_scores GROUP BY risk_tier ORDER BY avg_prob DESC")
roi      = q("SELECT * FROM roi_summary LIMIT 1").iloc[0]

# ════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════
st.markdown(f"""
<div style='background:{CARD};border:1px solid {BORDER};border-radius:16px;
            padding:44px 48px 40px;margin-bottom:24px'>
  <div class='eyebrow'>Portfolio Project &nbsp;·&nbsp; Music Streaming Analytics</div>
  <div class='headline'>KKBox Subscription Retention<br>&amp; Churn Analysis</div>
  <div class='subhead'>
    Retention analysis across <b style='color:{WHITE}'>970,960 subscribers</b>
    on Asia's leading music streaming platform. Who is churning,
    why are they leaving, and which users should we act on first?
  </div>
  <div style='margin:20px 0 28px'>
    <span class='pill'>Python</span>
    <span class='pill'>SQL</span>
    <span class='pill'>XGBoost</span>
    <span class='pill'>SHAP</span>
    <span class='pill'>Azure</span>
    <span class='pill'>Streamlit</span>
    <span class='pill' style='border-color:{GREEN};color:{GREEN}'>AUC 0.9876</span>
    <span class='pill' style='border-color:{ACCENT};color:{ACCENT}'>5-fold CV ±0.0003</span>
  </div>
  <div class='stat-row'>
    <div class='stat-item' style='border-color:{GREEN}'>
      <div class='stat-label'>Users Analysed</div>
      <div class='stat-value'>{int(ov['total']):,}</div>
    </div>
    <div class='stat-item' style='border-color:{RED}'>
      <div class='stat-label'>Churn Rate</div>
      <div class='stat-value'>{ov['churn']}%</div>
    </div>
    <div class='stat-item' style='border-color:{AMBER}'>
      <div class='stat-label'>Avg Rev · Retained</div>
      <div class='stat-value'>TWD {ov['rev_ret']:,.0f}</div>
    </div>
    <div class='stat-item' style='border-color:{ACCENT}'>
      <div class='stat-label'>Avg Rev · Churned</div>
      <div class='stat-value' style='color:{RED}'>TWD {ov['rev_ch']:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class='finding finding-red' style='margin-bottom:32px'>
  <b style='color:{WHITE}'>The headline finding:</b>&nbsp;
  Churned users paid <b style='color:{RED}'>3× more</b> than retained users
  (TWD {ov['rev_ch']:,.0f} vs TWD {ov['rev_ret']:,.0f}).
  Users without auto-renew churn at <b style='color:{RED}'>30.6%</b> —
  versus <b style='color:{GREEN}'>3.8%</b> with auto-renew on.
  This is a <b style='color:{WHITE}'>payments and subscription management problem,
  not an engagement problem.</b>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Cohort Retention",
    "🔍  Churn Drivers",
    "🎯  Risk Scoring",
    "🧪  Model Validation",
    "💡  Recommendations",
])

# ── TAB 1 ──────────────────────────────────────────
with tab1:
    avg_r = cohort['retention_rate'].mean()
    best  = cohort.loc[cohort['retention_rate'].idxmax()]

    st.markdown(f"<div class='chart-hed'>Older cohorts retain slightly better — but retention is stable across all signup months</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-dek'>Each row represents one month of new signups. Colour shows retention rate: red = below the {avg_r:.1f}% average, green = above. Split into two panels so every cohort is readable.</div>", unsafe_allow_html=True)

    mid  = len(cohort) // 2
    c1, c2 = st.columns(2)

    def chrt(df_s):
        f = px.bar(df_s, x="retention_rate", y="cohort", orientation='h',
                   color="retention_rate",
                   color_continuous_scale=[[0,RED],[0.5,AMBER],[1,GREEN]],
                   text=df_s['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                   labels={"retention_rate":"Retention (%)","cohort":""},
                   height=500)
        f.update_traces(textposition='outside', textfont=dict(size=12, color=WHITE))
        f.update_layout(coloraxis_showscale=False, xaxis_range=[80,103],
                        yaxis={'categoryorder':'category ascending'})
        return C(f)

    with c1:
        st.plotly_chart(chrt(cohort.iloc[mid:]), use_container_width=True)
    with c2:
        st.plotly_chart(chrt(cohort.iloc[:mid]), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Average Retention Rate",  f"{avg_r:.1f}%")
    m2.metric("Best Cohort",  str(best['cohort']),  f"{best['retention_rate']:.1f}%")
    m3.metric("Cohorts Tracked",  str(len(cohort)))

    st.markdown(f"""
    <div class='finding'>
      <b style='color:{WHITE}'>So what?</b> Retention hasn't meaningfully declined
      over time — this isn't a product deterioration story. The variation between
      cohorts tracks more closely with <i>which acquisition channels</i> were
      active in those months, which we explore in the Churn Drivers tab.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2 ──────────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div class='finding finding-amber' style='margin-bottom:32px'>
      <b style='color:{WHITE}'>Before you look at the charts:</b> we tested whether
      churned users simply stopped listening before they left. They didn't.
      Listening time, completion rate, and active days are nearly identical between
      churned and retained users. <b style='color:{WHITE}'>Every dominant churn signal
      is about payments and subscription structure — not product engagement.</b>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-hed'>Auto-renew OFF users churn at 8× the rate of auto-renew ON users</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-dek'>This is the single strongest signal in the entire dataset. Users who opted out of auto-renewal are far more likely to churn — regardless of how much they listen.</div>", unsafe_allow_html=True)
        f2 = px.bar(auto_df, x="status", y="churn_pct", color="status",
                    color_discrete_map={"Auto-renew ON":GREEN,"Auto-renew OFF":RED},
                    text=auto_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","status":""},
                    height=360)
        f2.update_traces(textposition='outside',
                         textfont=dict(size=18, color=WHITE), width=0.45)
        f2.update_layout(showlegend=False, yaxis_range=[0,40])
        st.plotly_chart(C(f2), use_container_width=True)

    with col2:
        st.markdown("<div class='chart-hed'>Longer discounted plans attract less loyal subscribers</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-dek'>Counter-intuitive: users on longer plans churn more. These are likely acquired via heavy discounts — low entry price, low commitment.</div>", unsafe_allow_html=True)
        plan_df['label'] = plan_df['payment_plan_days'].apply(
            lambda x: {7:"7 days",30:"30 days",90:"3 months",
                       180:"6 months",365:"1 year"}.get(int(x),f"{int(x)}d"))
        f3 = px.bar(plan_df, x="label", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=plan_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","label":""},
                    height=360)
        f3.update_traces(textposition='outside',
                         textfont=dict(size=16, color=WHITE))
        f3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(C(f3), use_container_width=True)

    st.divider()

    col3, col4 = st.columns([3,2])

    with col3:
        st.markdown("<div class='chart-hed'>The model confirms it — payment features dominate, listening features don't</div>", unsafe_allow_html=True)
        img(ASSETS_PATH/"shap_importance.png",
            "SHAP feature importance ranking. Payment method, plan price, and "
            "registration channel are the top predictors. Listening metrics "
            "(total_secs, completion_rate, avg_secs_per_day) are near the bottom — "
            "confirming the engagement hypothesis is wrong.")

    with col4:
        st.markdown("<div class='chart-hed'>Acquisition channel predicts churn — some channels are 5× worse than others</div>", unsafe_allow_html=True)
        st.markdown("<div class='chart-dek'>Channel IDs represent anonymised sign-up pathways (app, web, partner bundles). KKBox hasn't published the mapping — but the churn rate difference is real and consistent.</div>", unsafe_allow_html=True)
        reg_df['ch'] = reg_df['registered_via'].apply(lambda x: f"Ch {int(x)}")
        f4 = px.bar(reg_df, x="ch", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=reg_df['churn_pct'].apply(lambda x: f"{x:.1f}%"),
                    labels={"churn_pct":"Churn (%)","ch":""},
                    height=400)
        f4.update_traces(textposition='outside',
                         textfont=dict(size=13, color=WHITE))
        f4.update_layout(coloraxis_showscale=False)
        st.plotly_chart(C(f4), use_container_width=True)

# ── TAB 3 ──────────────────────────────────────────
with tab3:
    tier_c = {"High Risk":RED,"Medium Risk":AMBER,"Low Risk":GREEN}

    st.markdown("<div class='chart-hed'>Every user scored by churn probability — three tiers, one clear intervention priority</div>", unsafe_allow_html=True)
    st.markdown("<div class='chart-dek'>The XGBoost model assigns each user a churn probability between 0 and 1. We bucket these into three actionable tiers. High Risk users are the immediate target — they have the highest probability of churning and the most revenue at stake.</div>", unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1,r2,r3], risk_df.iterrows()):
        clr = tier_c.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{CARD};border:1px solid {BORDER};
                        border-top:4px solid {clr};border-radius:12px;
                        padding:26px 28px'>
              <div style='font-size:12px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.12em;color:{clr};margin-bottom:14px'>
                {row['risk_tier']}
              </div>
              <div style='font-size:38px;font-weight:700;color:{WHITE};
                          line-height:1;margin-bottom:4px'>
                {int(row['users']):,}
              </div>
              <div style='font-size:14px;color:{SUB};margin-bottom:18px'>users</div>
              <div style='font-size:14px;color:{SUB};line-height:2'>
                Avg churn probability
                <b style='color:{clr};font-size:16px'> {row['avg_prob']}%</b><br>
                Revenue at risk
                <b style='color:{WHITE};font-size:15px'> TWD {row['rev_at_risk']:,.0f}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    rc1, rc2 = st.columns(2)
    tiers = risk_df['risk_tier'].tolist()
    clrs  = [tier_c.get(t,MUTED) for t in tiers]

    with rc1:
        st.markdown("<div class='chart-hed'>Users per tier</div>", unsafe_allow_html=True)
        counts = risk_df['users'].tolist()
        f5 = go.Figure(go.Bar(
            x=tiers, y=counts, marker_color=clrs,
            text=[f"{v:,}" for v in counts],
            textposition='outside',
            textfont=dict(color=WHITE, size=15)))
        f5.update_layout(yaxis_title="Users", showlegend=False)
        st.plotly_chart(C(f5, 360), use_container_width=True)

    with rc2:
        st.markdown("<div class='chart-hed'>Revenue at risk per tier</div>", unsafe_allow_html=True)
        rev = risk_df['rev_at_risk'].tolist()
        f6 = go.Figure(go.Bar(
            x=tiers, y=rev, marker_color=clrs,
            text=[f"TWD {v:,.0f}" for v in rev],
            textposition='outside',
            textfont=dict(color=WHITE, size=13)))
        f6.update_layout(yaxis_title="TWD", showlegend=False)
        st.plotly_chart(C(f6, 360), use_container_width=True)

    st.markdown(f"""
    <div class='finding'>
      <b style='color:{WHITE}'>Intervention priority:</b> The 19,869 high-risk users
      represent the highest concentration of churn probability AND the highest
      revenue at stake. A targeted auto-renew incentive campaign on this group
      costs TWD {roi['cost_of_campaign']:,.0f} and protects an estimated
      TWD {roi['revenue_saved']:,.0f} — a <b style='color:{GREEN}'>{roi['roi_ratio']}x return.</b>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 4 ──────────────────────────────────────────
with tab4:
    # Model summary bar
    st.markdown(f"""
    <div style='background:{CARD};border:1px solid {BORDER};border-radius:12px;
                padding:26px 30px;margin-bottom:32px'>
      <div class='eyebrow'>Model Performance Summary</div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);
                  gap:24px;margin-top:16px'>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:700;margin-bottom:6px'>Hold-out AUC</div>
          <div style='font-size:32px;font-weight:700;color:{GREEN}'>0.9876</div>
          <div style='font-size:13px;color:{SUB}'>on unseen test data</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:700;margin-bottom:6px'>5-Fold CV Mean</div>
          <div style='font-size:32px;font-weight:700;color:{GREEN}'>0.9875</div>
          <div style='font-size:13px;color:{SUB}'>confirms no overfitting</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:700;margin-bottom:6px'>CV Std Deviation</div>
          <div style='font-size:32px;font-weight:700;color:{WHITE}'>±0.0003</div>
          <div style='font-size:13px;color:{SUB}'>extremely stable</div>
        </div>
        <div>
          <div style='font-size:12px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.1em;font-weight:700;margin-bottom:6px'>Optimal F1 Score</div>
          <div style='font-size:32px;font-weight:700;color:{WHITE}'>0.849</div>
          <div style='font-size:13px;color:{SUB}'>at threshold 0.85</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2)

    with mv1:
        st.markdown("<div class='chart-hed'>XGBoost outperforms a Logistic Regression baseline by +0.085 AUC</div>", unsafe_allow_html=True)
        img(ASSETS_PATH/"model_comparison.png",
            "We always test a simple baseline first. Logistic Regression (linear model) "
            "achieves AUC 0.9028. XGBoost reaches 0.9876 — the gap confirms that "
            "subscription churn has non-linear patterns a linear model can't capture.")

    with mv2:
        st.markdown("<div class='chart-hed'>AUC 0.9876 is stable across all 5 folds — not a lucky split</div>", unsafe_allow_html=True)
        img(ASSETS_PATH/"cross_validation.png",
            "5-fold stratified cross-validation re-trains the model on different data "
            "splits. All 5 folds score between 0.9871 and 0.9880 — a range of just 0.0009. "
            "This proves the model generalises, not just memorises.")

    st.divider()

    mv3, mv4 = st.columns(2)

    with mv3:
        st.markdown("<div class='chart-hed'>The default decision threshold is not optimal for churn</div>", unsafe_allow_html=True)
        img(ASSETS_PATH/"threshold_analysis.png",
            "Most classifiers predict at threshold 0.5 by default. For churn, "
            "missing a churner (false negative) is more costly than flagging "
            "someone who stays (false positive). At threshold 0.85, F1 improves "
            "from 0.729 to 0.849.")

    with mv4:
        st.markdown("<div class='chart-hed'>SHAP shows exactly how each feature pushes a user toward or away from churn</div>", unsafe_allow_html=True)
        img(ASSETS_PATH/"shap_beeswarm.png",
            "Each dot is one user. Red = high feature value, blue = low. "
            "Dots to the right increase churn probability. "
            "Auto-renew OFF (blue dots far right) is the dominant signal — "
            "even more important than how much someone pays or how long they've been subscribed.")

    st.divider()
    st.markdown("<div class='chart-hed'>Auto-renew OFF sharply increases predicted churn — regardless of any other factor</div>", unsafe_allow_html=True)
    img(ASSETS_PATH/"shap_dependence_autorenew.png",
        "SHAP dependence plot for auto-renew. Left cluster = auto-renew OFF (value 0), "
        "right = auto-renew ON (value 1). Users with auto-renew OFF have SHAP values "
        "between 0.5 and 3.5 — meaning the model pushes their churn probability "
        "significantly higher. This is the most actionable feature: one behaviour change "
        "that dramatically reduces predicted churn.")

# ── TAB 5 ──────────────────────────────────────────
with tab5:
    # ROI hero
    st.markdown(f"""
    <div style='background:{CARD};border:1px solid {BORDER};
                border-top:4px solid {GREEN};border-radius:12px;
                padding:34px 38px;margin-bottom:32px'>
      <div class='eyebrow' style='color:{GREEN}'>Business Case · Modelled ROI</div>
      <div style='font-family:DM Serif Display,serif;font-size:1.8rem;
                  color:{WHITE};margin:12px 0 14px;line-height:1.35'>
        A targeted 10% auto-renew incentive to
        <span style='color:{GREEN}'>{int(roi['n_high_risk']):,} high-risk users</span>
        costs <span style='color:{AMBER}'>TWD {roi['cost_of_campaign']:,.0f}</span>
        and protects
        <span style='color:{GREEN}'>TWD {roi['revenue_saved']:,.0f}</span>
        in subscriber revenue.
      </div>
      <div style='font-size:14px;color:{SUB};line-height:1.8;max-width:720px'>
        Assumes 30% conversion rate — conservative, based on the observed 8× churn
        rate difference between auto-renew OFF (30.6%) and ON (3.8%) users.
        Every TWD 1 spent on the campaign saves <b style='color:{GREEN}'>
        TWD {roi['roi_ratio']}</b> in retained revenue.
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
            "title":"Give users a reason to turn auto-renew on",
            "finding":"Auto-renew OFF is the single strongest churn predictor in the model — 8× higher churn rate than auto-renew ON. It isn't about engagement: these users listen just as much. They just haven't committed to renewing.",
            "action":f"Offer a permanent 10% discount to any user who enables auto-renew. Cost of discount is far lower than cost of reacquisition. Targeting the {int(roi['n_high_risk']):,} high-risk users first yields a modelled {roi['roi_ratio']}x ROI.",
        },
        {
            "num":"02","color":AMBER,"label":"REVENUE PROTECTION",
            "title":"Stop using deep discounts to sell long plans",
            "finding":"Churned users paid TWD 383 on average vs TWD 129 for retained users. Long discounted plans attract subscribers who cancel once the deal expires — not loyal users.",
            "action":"Redirect discount budget from long-plan acquisition to loyalty rewards for existing monthly subscribers. Acquire fewer users but retain them longer.",
        },
        {
            "num":"03","color":ACCENT,"label":"ACQUISITION QUALITY",
            "title":"Audit and reallocate acquisition channel spend",
            "finding":"The highest-churn acquisition channel produces users who churn at over 5× the rate of the lowest-churn channel. Acquisition channel is the third strongest churn predictor in SHAP.",
            "action":"Identify which channels map to the high-churn IDs and reduce spend there. Reinvest in channels that produce loyal users — even if the upfront volume is lower.",
        },
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORDER};
                    border-left:4px solid {rec["color"]};
                    border-radius:0 12px 12px 0;
                    padding:26px 30px;margin-bottom:16px'>
          <div style='display:flex;align-items:baseline;gap:18px;margin-bottom:14px'>
            <span style='font-size:28px;font-weight:700;color:{rec["color"]};
                         opacity:0.2'>{rec["num"]}</span>
            <div>
              <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.12em;color:{rec["color"]};margin-bottom:3px'>
                {rec["label"]}
              </div>
              <div style='font-size:18px;font-weight:700;color:{WHITE}'>
                {rec["title"]}
              </div>
            </div>
          </div>
          <div style='padding-left:50px'>
            <p style='font-size:14px;color:{SUB};margin:0 0 10px;line-height:1.8'>
              <b style='color:{TEXT}'>Finding:&nbsp;</b>{rec["finding"]}
            </p>
            <p style='font-size:14px;color:{SUB};margin:0;line-height:1.8'>
              <b style='color:{TEXT}'>Action:&nbsp;</b>{rec["action"]}
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <p style='font-size:13px;color:{MUTED};text-align:center;line-height:2'>
    WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
    XGBoost AUC 0.9876 · 5-fold CV 0.9875 ±0.0003 &nbsp;·&nbsp;
    Built by Akanksha Nayak
    </p>
    """, unsafe_allow_html=True)