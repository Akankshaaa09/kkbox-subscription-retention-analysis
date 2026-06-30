# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard — Final Version
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
BG      = "#0C0C0E"
CARD    = "#13131A"
CARD2   = "#1A1A24"
CARD3   = "#20202C"
BORDER  = "#2C2C3E"
GREEN   = "#00C48C"
RED     = "#FF5C5C"
AMBER   = "#FFB547"
BLUE    = "#4B9EFF"
TEXT    = "#F0F0F5"
BODY    = "#C8C8D8"
MUTED   = "#7070A0"
ACCENT  = "#9B7FFF"
WHITE   = "#FFFFFF"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

  html, body, [class*="css"] {{
      font-family: 'Sora', sans-serif !important;
      background-color: {BG};
      color: {TEXT};
  }}
  .stApp {{ background-color: {BG}; }}
  .block-container {{ padding-top: 2rem !important; max-width: 1280px; }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 0;
      background: {CARD};
      padding: 0 8px;
      border-radius: 14px;
      border: 1px solid {BORDER};
      margin-bottom: 36px;
  }}
  .stTabs [data-baseweb="tab"] {{
      font-family: 'Sora', sans-serif !important;
      font-size: 14px;
      font-weight: 500;
      color: {MUTED};
      background: transparent;
      padding: 14px 26px;
      border: none;
      border-radius: 10px;
      margin: 4px 2px;
  }}
  .stTabs [aria-selected="true"] {{
      color: {WHITE} !important;
      background: {CARD2} !important;
      font-weight: 600 !important;
      border: 1px solid {BORDER} !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{ color: {TEXT} !important; }}

  /* ── Metrics ── */
  div[data-testid="metric-container"] {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 22px 24px;
  }}
  div[data-testid="metric-container"] label {{
      color: {MUTED} !important;
      font-size: 11px !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      letter-spacing: 0.12em;
  }}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
      color: {WHITE} !important;
      font-family: 'Sora', sans-serif !important;
      font-size: 28px !important;
      font-weight: 700 !important;
  }}
  div[data-testid="stMetricDelta"] span {{
      font-size: 13px !important;
  }}

  hr {{ border-color: {BORDER} !important; margin: 32px 0 !important; }}

  /* ── Type helpers ── */
  .eyebrow {{
      font-size: 11px; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.15em;
      color: {MUTED}; margin-bottom: 10px;
  }}
  .display {{
      font-family: 'Playfair Display', serif;
      font-size: 2.6rem; font-weight: 700;
      color: {WHITE}; line-height: 1.15; margin-bottom: 18px;
  }}
  .lead {{
      font-size: 15px; color: {BODY};
      line-height: 1.8; max-width: 660px;
  }}
  .pill {{
      display: inline-block;
      background: {CARD2}; border: 1px solid {BORDER};
      border-radius: 20px; padding: 5px 16px;
      font-size: 12px; font-weight: 600;
      color: {BODY}; margin: 3px 2px;
  }}
  /* Chart card */
  .chart-card {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 24px 24px 16px;
      margin-bottom: 4px;
  }}
  .chart-hed {{
      font-size: 15px; font-weight: 700;
      color: {WHITE}; line-height: 1.4;
      margin-bottom: 6px;
  }}
  .chart-dek {{
      font-size: 13px; color: {BODY};
      line-height: 1.7; margin-bottom: 16px;
  }}
  /* Insight box */
  .insight {{
      background: {CARD2}; border: 1px solid {BORDER};
      border-left: 3px solid {GREEN};
      border-radius: 0 12px 12px 0;
      padding: 18px 22px; margin: 20px 0;
      font-size: 14px; color: {BODY}; line-height: 1.8;
  }}
  .insight b {{ color: {WHITE}; }}
  .insight-amber {{ border-left-color: {AMBER}; }}
  .insight-blue  {{ border-left-color: {BLUE}; }}
  /* Image card — dark with label */
  .img-card {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 14px;
      overflow: hidden;
      margin-bottom: 4px;
  }}
  .img-card-label {{
      font-size: 11px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.12em;
      padding: 10px 18px;
      border-bottom: 1px solid {BORDER};
  }}
  .img-card-inner {{
      background: #F5F5F7;
      padding: 16px;
  }}
  .img-cap {{
      font-size: 13px; color: {BODY};
      line-height: 1.7; padding: 14px 18px 16px;
  }}
  /* Stat row */
  .stat-row {{
      display: grid;
      grid-template-columns: repeat(4,1fr);
      gap: 20px; margin-top: 28px;
  }}
  .stat-item {{ border-left: 3px solid; padding-left: 16px; }}
  .stat-label {{
      font-size: 11px; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: {MUTED}; margin-bottom: 4px;
  }}
  .stat-value {{
      font-size: 26px; font-weight: 700; color: {WHITE};
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

def C(fig, h=400):
    fig.update_layout(
        height=h,
        plot_bgcolor=CARD2, paper_bgcolor=CARD,
        font=dict(color=BODY, family="Sora", size=12),
        margin=dict(t=8, b=8, l=8, r=8),
        title=None,
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=BODY, size=11)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=BODY, size=11)),
        legend=dict(bgcolor=CARD2, bordercolor=BORDER,
                    font=dict(color=BODY, size=12))
    )
    return fig

def chart_card(hed, dek, fig, h=380):
    st.markdown(f"""
    <div class='chart-card'>
      <div class='chart-hed'>{hed}</div>
      <div class='chart-dek'>{dek}</div>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(C(fig, h), use_container_width=True)

def img_card(label, label_color, path, caption):
    st.markdown(f"""
    <div class='img-card'>
      <div class='img-card-label' style='color:{label_color}'>
        {label}
      </div>
      <div class='img-card-inner'>
    """, unsafe_allow_html=True)
    st.image(str(path), use_column_width=True)
    st.markdown(f"""
      </div>
      <div class='img-cap'>{caption}</div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════
ov      = q("SELECT COUNT(*) total, ROUND(AVG(is_churn)*100,2) churn, ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) rev_ret, ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) rev_ch FROM users").iloc[0]
cohort  = q("SELECT cohort, cohort_size, retained, retention_rate FROM cohort_retention WHERE cohort>='2015-01' ORDER BY cohort")
auto_df = q("SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew ON' ELSE 'Auto-renew OFF' END status, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE is_auto_renew IS NOT NULL GROUP BY is_auto_renew ORDER BY is_auto_renew DESC")
plan_df = q("SELECT payment_plan_days, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE payment_plan_days IN (7,30,90,180,365) GROUP BY payment_plan_days ORDER BY payment_plan_days")
reg_df  = q("SELECT registered_via, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE registered_via IS NOT NULL GROUP BY registered_via ORDER BY churn_pct DESC")
risk_df = q("SELECT risk_tier, COUNT(*) users, ROUND(AVG(churn_probability)*100,1) avg_prob, ROUND(SUM(churn_probability*plan_list_price),0) rev_at_risk FROM risk_scores GROUP BY risk_tier ORDER BY avg_prob DESC")
roi     = q("SELECT * FROM roi_summary LIMIT 1").iloc[0]

# ════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════
st.markdown(f"""
<div style='background:{CARD};border:1px solid {BORDER};border-radius:16px;
            padding:44px 48px 40px;margin-bottom:20px'>
  <div class='eyebrow'>Portfolio Project &nbsp;·&nbsp; Music Streaming Analytics</div>
  <div class='display'>KKBox Subscription Retention<br>&amp; Churn Analysis</div>
  <div class='lead'>
    Retention analysis across <b style='color:{WHITE}'>970,960 subscribers</b>
    on Asia's leading music streaming platform — who is churning,
    why are they leaving, and which users should we act on first?
  </div>
  <div style='margin:20px 0 28px'>
    <span class='pill'>Python</span><span class='pill'>SQL</span>
    <span class='pill'>XGBoost</span><span class='pill'>SHAP</span>
    <span class='pill'>Azure</span><span class='pill'>Streamlit</span>
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
<div class='insight' style='margin-bottom:28px'>
  <b>The headline finding:</b> Churned users paid
  <b style='color:{RED}'>3× more</b> than retained users
  (TWD {ov['rev_ch']:,.0f} vs TWD {ov['rev_ret']:,.0f}).
  Users without auto-renew churn at <b style='color:{RED}'>30.6%</b>
  vs <b style='color:{GREEN}'>3.8%</b> with auto-renew on —
  an 8× gap. <b>This is a payments and subscription management problem,
  not an engagement problem.</b>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Cohort Retention",
    "🔍  Churn Drivers",
    "🎯  Risk Scoring",
    "🧪  Model Validation",
    "💡  Recommendations",
])

# ── TAB 1 ────────────────────────────────────
with tab1:
    avg_r = cohort['retention_rate'].mean()
    best  = cohort.loc[cohort['retention_rate'].idxmax()]

    st.markdown(f"""
    <div class='chart-hed' style='font-size:18px;margin-bottom:6px'>
      Retention is stable — older cohorts retain slightly better
    </div>
    <div class='chart-dek' style='font-size:14px'>
      Each row = one month of new signups. Colour shows whether that cohort
      retained above or below the {avg_r:.1f}% average.
      Split into two panels so every cohort is readable at a glance.
    </div>
    """, unsafe_allow_html=True)

    mid = len(cohort) // 2
    c1, c2 = st.columns(2)

    def cohort_fig(df_s):
        f = px.bar(df_s, x="retention_rate", y="cohort", orientation='h',
                   color="retention_rate",
                   color_continuous_scale=[[0,RED],[0.5,AMBER],[1,GREEN]],
                   text=df_s['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                   labels={"retention_rate":"Retention (%)","cohort":""},
                   height=500)
        f.update_traces(textposition='outside',
                        textfont=dict(size=11, color=WHITE))
        f.update_layout(coloraxis_showscale=False,
                        xaxis_range=[80,103], title=None,
                        yaxis={'categoryorder':'category ascending'})
        return C(f, 500)

    with c1:
        st.plotly_chart(cohort_fig(cohort.iloc[mid:]), use_container_width=True)
    with c2:
        st.plotly_chart(cohort_fig(cohort.iloc[:mid]), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Average Retention",  f"{avg_r:.1f}%")
    m2.metric("Best Cohort", str(best['cohort']), f"{best['retention_rate']:.1f}%")
    m3.metric("Cohorts Tracked", str(len(cohort)))

    st.markdown(f"""
    <div class='insight'>
      <b>So what?</b> Retention hasn't meaningfully declined over time —
      this isn't a product deterioration story. The variation between cohorts
      tracks more closely with which acquisition channels were active in those
      months, explored in the Churn Drivers tab.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2 ────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div class='insight insight-amber' style='margin-bottom:28px'>
      <b>Before the charts:</b> We tested whether churned users simply stopped
      listening before they left. They didn't. Listening time, completion rate,
      and active days are nearly identical between churned and retained users.
      <b>Every dominant churn signal is about payments — not product engagement.</b>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        auto_fig = px.bar(auto_df, x="status", y="churn_pct",
                    color="status",
                    color_discrete_map={"Auto-renew ON":GREEN,"Auto-renew OFF":RED},
                    text=auto_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","status":""})
        auto_fig.update_traces(textposition='outside',
                         textfont=dict(size=17, color=WHITE), width=0.45)
        auto_fig.update_layout(showlegend=False, yaxis_range=[0,38], title=None)
        chart_card(
            "Auto-renew OFF users churn at 8× the rate of auto-renew ON",
            "The single strongest predictor in the model. Users who opted out of auto-renewal are far more likely to churn — regardless of how much they listen.",
            auto_fig, 360
        )

    with col2:
        plan_df['label'] = plan_df['payment_plan_days'].apply(
            lambda x: {7:"7 days",30:"30 days",90:"3 months",
                       180:"6 months",365:"1 year"}.get(int(x),f"{int(x)}d"))
        plan_fig = px.bar(plan_df, x="label", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=plan_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct":"Churn Rate (%)","label":""})
        plan_fig.update_traces(textposition='outside',
                         textfont=dict(size=15, color=WHITE))
        plan_fig.update_layout(coloraxis_showscale=False, title=None)
        chart_card(
            "Longer discounted plans attract less loyal subscribers",
            "Counter-intuitive but consistent: users on longer plans churn more. These are likely acquired via heavy discounts — low entry price, low commitment.",
            plan_fig, 360
        )

    st.divider()

    col3, col4 = st.columns([3,2])

    with col3:
        img_card(
            "SHAP Feature Importance — What the Model Learned",
            GREEN,
            ASSETS_PATH/"shap_importance.png",
            "Payment method, plan price, and registration channel dominate. "
            "Listening metrics (total_secs, completion_rate, avg_secs_per_day) "
            "are near the bottom — the engagement hypothesis is wrong."
        )

    with col4:
        reg_df['ch'] = reg_df['registered_via'].apply(lambda x: f"Ch {int(x)}")
        reg_fig = px.bar(reg_df, x="ch", y="churn_pct",
                    color="churn_pct",
                    color_continuous_scale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                    text=reg_df['churn_pct'].apply(lambda x: f"{x:.1f}%"),
                    labels={"churn_pct":"Churn (%)","ch":""})
        reg_fig.update_traces(textposition='outside',
                         textfont=dict(size=12, color=WHITE))
        reg_fig.update_layout(coloraxis_showscale=False, title=None)
        chart_card(
            "Acquisition channel predicts churn — 5× gap between best and worst",
            "Channel IDs are anonymised sign-up pathways (app, web, partner bundles). KKBox hasn't published the mapping — but the churn rate difference is real.",
            reg_fig, 420
        )

# ── TAB 3 ────────────────────────────────────
with tab3:
    tier_c = {"High Risk":RED,"Medium Risk":AMBER,"Low Risk":GREEN}

    st.markdown(f"""
    <div class='chart-hed' style='font-size:18px;margin-bottom:6px'>
      Every user scored by churn probability — three tiers, one clear priority
    </div>
    <div class='chart-dek' style='font-size:14px;margin-bottom:24px'>
      The XGBoost model assigns each user a churn probability between 0 and 1.
      High Risk users have the highest probability of churning and the most
      revenue at stake — they are the immediate intervention target.
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1,r2,r3], risk_df.iterrows()):
        clr = tier_c.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{CARD};border:1px solid {BORDER};
                        border-top:3px solid {clr};border-radius:14px;
                        padding:26px 28px'>
              <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.14em;color:{clr};margin-bottom:14px'>
                {row['risk_tier']}
              </div>
              <div style='font-size:40px;font-weight:700;color:{WHITE};line-height:1'>
                {int(row['users']):,}
              </div>
              <div style='font-size:13px;color:{MUTED};margin-bottom:18px'>users</div>
              <div style='border-top:1px solid {BORDER};padding-top:14px'>
                <div style='font-size:13px;color:{BODY};line-height:2.2'>
                  Avg churn probability<br>
                  <span style='font-size:22px;font-weight:700;
                               color:{clr}'>{row['avg_prob']}%</span>
                </div>
                <div style='font-size:13px;color:{BODY};margin-top:8px;line-height:2'>
                  Revenue at risk<br>
                  <span style='font-size:18px;font-weight:700;
                               color:{WHITE}'>TWD {row['rev_at_risk']:,.0f}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    rc1, rc2 = st.columns(2)
    tiers = risk_df['risk_tier'].tolist()
    clrs  = [tier_c.get(t,MUTED) for t in tiers]

    with rc1:
        f5 = go.Figure(go.Bar(
            x=tiers, y=risk_df['users'].tolist(),
            marker_color=clrs,
            text=[f"{v:,}" for v in risk_df['users'].tolist()],
            textposition='outside',
            textfont=dict(color=WHITE, size=14)))
        f5.update_layout(yaxis_title="Users", showlegend=False, title=None)
        chart_card("Users per risk tier", "High risk users are the minority but carry the most intervention value.", f5, 340)

    with rc2:
        f6 = go.Figure(go.Bar(
            x=tiers, y=risk_df['rev_at_risk'].tolist(),
            marker_color=clrs,
            text=[f"TWD {v:,.0f}" for v in risk_df['rev_at_risk'].tolist()],
            textposition='outside',
            textfont=dict(color=WHITE, size=12)))
        f6.update_layout(yaxis_title="TWD", showlegend=False, title=None)
        chart_card("Revenue at risk per tier", "High risk users account for the largest share of revenue at stake despite being the smallest group.", f6, 340)

    st.markdown(f"""
    <div class='insight'>
      <b>Intervention priority:</b> The 19,869 high-risk users represent the
      highest concentration of churn probability AND the highest revenue at stake.
      A targeted auto-renew incentive on this group costs
      <b style='color:{AMBER}'>TWD {roi['cost_of_campaign']:,.0f}</b> and protects
      <b style='color:{GREEN}'>TWD {roi['revenue_saved']:,.0f}</b> —
      a <b style='color:{GREEN}'>{roi['roi_ratio']}x return.</b>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 4 ────────────────────────────────────
with tab4:
    # Summary strip
    st.markdown(f"""
    <div style='background:{CARD};border:1px solid {BORDER};border-radius:14px;
                padding:28px 32px;margin-bottom:32px'>
      <div class='eyebrow'>Model Performance Summary</div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);
                  gap:24px;margin-top:16px'>
        <div style='border-left:3px solid {GREEN};padding-left:16px'>
          <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;color:{MUTED};margin-bottom:6px'>Hold-out AUC</div>
          <div style='font-size:32px;font-weight:700;color:{GREEN}'>0.9876</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>on unseen test data</div>
        </div>
        <div style='border-left:3px solid {GREEN};padding-left:16px'>
          <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;color:{MUTED};margin-bottom:6px'>5-Fold CV Mean</div>
          <div style='font-size:32px;font-weight:700;color:{GREEN}'>0.9875</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>confirms no overfitting</div>
        </div>
        <div style='border-left:3px solid {BLUE};padding-left:16px'>
          <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;color:{MUTED};margin-bottom:6px'>CV Std Deviation</div>
          <div style='font-size:32px;font-weight:700;color:{WHITE}'>±0.0003</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>extremely stable</div>
        </div>
        <div style='border-left:3px solid {AMBER};padding-left:16px'>
          <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;color:{MUTED};margin-bottom:6px'>Optimal F1 Score</div>
          <div style='font-size:32px;font-weight:700;color:{WHITE}'>0.849</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>at threshold 0.85</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2)

    with mv1:
        img_card(
            "Baseline vs XGBoost",
            BLUE,
            ASSETS_PATH/"model_comparison.png",
            "Logistic Regression baseline: AUC 0.9028. XGBoost: 0.9876. "
            "The +0.085 gap confirms that subscription churn has non-linear "
            "patterns a linear model can't capture."
        )

    with mv2:
        img_card(
            "5-Fold Cross-Validation Stability",
            GREEN,
            ASSETS_PATH/"cross_validation.png",
            "All 5 folds score between 0.9871 and 0.9880 — a range of 0.0009. "
            "AUC 0.9876 is not a lucky train/test split. "
            "The model generalises."
        )

    st.divider()

    mv3, mv4 = st.columns(2)

    with mv3:
        img_card(
            "Threshold Optimisation",
            AMBER,
            ASSETS_PATH/"threshold_analysis.png",
            "Default threshold 0.5 gives F1 0.729. "
            "Optimal threshold 0.85 gives F1 0.849. "
            "For churn, missing a churner costs more than a false alarm."
        )

    with mv4:
        img_card(
            "SHAP Beeswarm — Direction per User",
            ACCENT,
            ASSETS_PATH/"shap_beeswarm.png",
            "Each dot = one user. Red = high feature value, blue = low. "
            "Dots to the right increase churn probability. "
            "Auto-renew and days_until_expiry dominate the right side."
        )

    st.divider()

    img_card(
        "SHAP Dependence — Auto-Renew Deep Dive",
        RED,
        ASSETS_PATH/"shap_dependence_autorenew.png",
        "Auto-renew is binary: 0 = OFF (left cluster), 1 = ON (right cluster). "
        "Users with auto-renew OFF have SHAP values between 0.5 and 3.5 — "
        "meaning the model pushes their churn probability significantly higher. "
        "This is the most actionable feature in the entire model: "
        "one behaviour change that dramatically reduces predicted churn."
    )

# ── TAB 5 ────────────────────────────────────
with tab5:
    # ROI hero
    st.markdown(f"""
    <div style='background:{CARD};border:1px solid {BORDER};
                border-top:3px solid {GREEN};border-radius:14px;
                padding:34px 38px;margin-bottom:28px'>
      <div class='eyebrow' style='color:{GREEN}'>Business Case · Modelled ROI</div>
      <div style='font-family:Playfair Display,serif;font-size:1.75rem;
                  font-weight:700;color:{WHITE};margin:14px 0 12px;line-height:1.35'>
        A 10% auto-renew incentive to
        <span style='color:{GREEN}'>{int(roi['n_high_risk']):,} high-risk users</span>
        costs <span style='color:{AMBER}'>TWD {roi['cost_of_campaign']:,.0f}</span>
        and protects
        <span style='color:{GREEN}'>TWD {roi['revenue_saved']:,.0f}</span>
        in subscriber revenue.
      </div>
      <div style='font-size:14px;color:{BODY};line-height:1.8;max-width:720px'>
        Assumes 30% conversion rate — conservative, based on the 8× churn rate
        difference between auto-renew OFF (30.6%) and ON (3.8%) users.
        Every TWD 1 spent on the campaign saves
        <b style='color:{GREEN}'>TWD {roi['roi_ratio']}</b> in retained revenue.
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
            "finding":"Auto-renew OFF is the single strongest churn predictor in the model — 8× higher churn rate than auto-renew ON. These users listen just as much. They just haven't committed to renewing.",
            "action":f"Offer a permanent 10% discount to any user who enables auto-renew. Cost of discount is far lower than cost of reacquisition. Targeting {int(roi['n_high_risk']):,} high-risk users first yields a modelled {roi['roi_ratio']}x ROI.",
        },
        {
            "num":"02","color":AMBER,"label":"REVENUE PROTECTION",
            "title":"Stop using deep discounts to sell long plans",
            "finding":"Churned users paid TWD 383 on average vs TWD 129 for retained users. Long discounted plans attract subscribers who cancel once the deal expires — not loyal users.",
            "action":"Redirect discount budget from long-plan acquisition to loyalty rewards for existing monthly subscribers. Acquire fewer users but retain them longer.",
        },
        {
            "num":"03","color":BLUE,"label":"ACQUISITION QUALITY",
            "title":"Audit and reallocate acquisition channel spend",
            "finding":"The highest-churn acquisition channel produces users who churn at over 5× the rate of the lowest-churn channel. Acquisition channel is the third strongest churn predictor in SHAP.",
            "action":"Identify which channels map to the high-churn IDs and reduce spend there. Reinvest in channels that produce loyal users — even if the upfront volume is lower.",
        },
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORDER};
                    border-left:4px solid {rec["color"]};
                    border-radius:0 14px 14px 0;
                    padding:26px 30px;margin-bottom:14px'>
          <div style='display:flex;align-items:baseline;gap:18px;margin-bottom:14px'>
            <span style='font-size:26px;font-weight:700;
                         color:{rec["color"]};opacity:0.2'>{rec["num"]}</span>
            <div>
              <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.14em;color:{rec["color"]};
                          margin-bottom:4px'>{rec["label"]}</div>
              <div style='font-size:18px;font-weight:700;
                          color:{WHITE}'>{rec["title"]}</div>
            </div>
          </div>
          <div style='padding-left:48px'>
            <p style='font-size:14px;color:{BODY};margin:0 0 10px;line-height:1.8'>
              <b style='color:{TEXT}'>Finding:&nbsp;</b>{rec["finding"]}
            </p>
            <p style='font-size:14px;color:{BODY};margin:0;line-height:1.8'>
              <b style='color:{TEXT}'>Action:&nbsp;</b>{rec["action"]}
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <p style='font-size:12px;color:{MUTED};text-align:center;line-height:2.2'>
    WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
    XGBoost AUC 0.9876 · 5-fold CV 0.9875 ±0.0003 &nbsp;·&nbsp;
    Built by Akanksha Nayak
    </p>
    """, unsafe_allow_html=True)