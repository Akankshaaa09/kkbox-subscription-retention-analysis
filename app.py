# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard, v2 (UI/UX revamp + campaign simulator)
# Author: Akanksha Nayak
# ============================================================
from pathlib import Path
import base64
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
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="KKBox Churn Analysis",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BG      = "#0C0C0E"
CARD    = "#13131A"
CARD2   = "#1A1A24"
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

CHART_H = 360

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

  /* ---------- Hide Streamlit chrome ---------- */
  #MainMenu, footer, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
  header[data-testid="stHeader"] {{ background: transparent !important; height: 0 !important; }}

  /* ---------- Motion ---------- */
  @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to   {{ opacity: 1; transform: none; }}
  }}
  .hero {{ animation: fadeUp .7s ease both; }}
  .stTabs [data-baseweb="tab-panel"] {{ animation: fadeUp .45s ease both; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{
      transition: transform .2s ease, box-shadow .2s ease;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 30px rgba(0,0,0,.35);
  }}
  @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; transition: none !important; }}
  }}

  /* ---------- Tabs ---------- */
  .stTabs [data-baseweb="tab-list"] {{
      gap: 0; background: {CARD}; padding: 0 8px;
      border-radius: 14px; border: 1px solid {BORDER};
      margin-bottom: 36px;
  }}
  .stTabs [data-baseweb="tab"] {{
      font-family: 'Sora', sans-serif !important;
      font-size: 14px; font-weight: 500; color: {MUTED};
      background: transparent; padding: 14px 26px;
      border: none; border-radius: 10px; margin: 4px 2px;
  }}
  .stTabs [aria-selected="true"] {{
      color: {WHITE} !important; background: {CARD2} !important;
      font-weight: 600 !important; border: 1px solid {BORDER} !important;
  }}
  .stTabs [data-baseweb="tab"]:hover {{ color: {TEXT} !important; }}
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

  /* ---------- Metrics ---------- */
  div[data-testid="stMetric"], div[data-testid="metric-container"] {{
      background: {CARD}; border: 1px solid {BORDER};
      border-radius: 12px; padding: 22px 24px;
  }}
  div[data-testid="stMetric"] label, div[data-testid="metric-container"] label {{
      color: {MUTED} !important; font-size: 11px !important;
      font-weight: 600 !important; text-transform: uppercase;
      letter-spacing: 0.12em;
  }}
  div[data-testid="stMetricValue"] {{
      color: {WHITE} !important; font-family: 'Sora', sans-serif !important;
      font-size: 28px !important; font-weight: 700 !important;
  }}
  div[data-testid="stMetricDelta"] span {{ font-size: 13px !important; }}

  hr {{ border-color: {BORDER} !important; margin: 32px 0 !important; }}

  /* ---------- Type ---------- */
  .eyebrow {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.15em; color: {MUTED}; margin-bottom: 10px;
  }}
  .display {{
      font-family: 'Playfair Display', serif; font-size: 2.7rem;
      font-weight: 700; color: {WHITE}; line-height: 1.15;
      margin-bottom: 18px; max-width: 900px;
  }}
  .display em {{ font-style: normal; color: {GREEN}; }}
  .lead {{ font-size: 15px; color: {BODY}; line-height: 1.8; max-width: 720px; }}
  .pill {{
      display: inline-block; background: {CARD2}; border: 1px solid {BORDER};
      border-radius: 20px; padding: 5px 16px; font-size: 12px;
      font-weight: 600; color: {BODY}; margin: 3px 2px;
  }}
  .section-hed {{ font-size: 18px; font-weight: 700; color: {WHITE}; margin-bottom: 8px; }}
  .section-dek {{ font-size: 14px; color: {BODY}; line-height: 1.8; margin-bottom: 20px; max-width: 820px; }}

  /* ---------- Cards ---------- */
  div[data-testid="stVerticalBlockBorderWrapper"] > div {{
      background: {CARD} !important;
      border: 1px solid {BORDER} !important;
      border-radius: 14px !important;
      padding: 20px 22px !important;
  }}
  .viz-card-tag {{
      display: block; font-size: 11px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 8px;
  }}
  .viz-card-hed {{ font-size: 16px; font-weight: 700; color: {WHITE}; line-height: 1.4; }}
  .viz-dek {{
      font-size: 13px; color: {BODY}; line-height: 1.7;
      padding-top: 14px; margin-top: 6px; border-top: 1px solid {BORDER};
  }}
  /* Static SHAP charts were exported on white; flip them to match the dark theme */
  .dark-img {{
      width: 100%; border-radius: 10px;
      filter: invert(0.93) hue-rotate(180deg);
  }}

  .insight {{
      background: {CARD2}; border: 1px solid {BORDER};
      border-left: 3px solid {GREEN}; border-radius: 0 12px 12px 0;
      padding: 18px 22px; margin: 20px 0; font-size: 14px;
      color: {BODY}; line-height: 1.8;
  }}
  .insight b {{ color: {WHITE}; }}
  .insight-amber {{ border-left-color: {AMBER}; }}
  .insight-blue  {{ border-left-color: {BLUE}; }}

  .stat-row {{
      display: grid; grid-template-columns: repeat(4,1fr);
      gap: 20px; margin-top: 28px;
  }}
  @media (max-width: 800px) {{
      .stat-row {{ grid-template-columns: repeat(2,1fr); }}
      .display {{ font-size: 2rem; }}
  }}
  .stat-item {{ border-left: 3px solid; padding-left: 16px; }}
  .stat-label {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.1em; color: {MUTED}; margin-bottom: 4px;
  }}
  .stat-value {{ font-size: 26px; font-weight: 700; color: {WHITE}; }}

  /* ---------- Simulator ---------- */
  .sim-hed {{
      font-family: 'Playfair Display', serif; font-size: 1.6rem;
      font-weight: 700; color: {WHITE}; line-height: 1.4; margin: 6px 0 10px;
  }}
  .sim-note {{ font-size: 12.5px; color: {MUTED}; line-height: 1.7; }}
</style>
""", unsafe_allow_html=True)

ASSETS_PATH = Path("assets")

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def q(sql):
    return pd.read_sql(sql, get_conn())

def style_chart(fig, h=CHART_H):
    fig.update_layout(
        height=h,
        title=dict(text=""),          # empty title instead of popping it (fixes 'undefined' labels)
        plot_bgcolor=CARD2, paper_bgcolor=CARD,
        font=dict(color=BODY, family="Sora", size=12),
        margin=dict(t=30, b=8, l=8, r=8),
        legend=dict(bgcolor=CARD2, bordercolor=BORDER, font=dict(color=BODY, size=12)),
        hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=dict(color=WHITE, family="Sora")),
    )
    fig.update_xaxes(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER,
                     tickfont=dict(color=BODY, size=11), title_font=dict(color=MUTED, size=11))
    fig.update_yaxes(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER,
                     tickfont=dict(color=BODY, size=11), title_font=dict(color=MUTED, size=11))
    fig.update_annotations(font=dict(color=BODY, size=12))
    return fig

def chart_card(tag, tag_color, hed, dek, fig, h=CHART_H):
    with st.container(border=True):
        st.markdown(f"""
        <span class='viz-card-tag' style='color:{tag_color}'>{tag}</span>
        <div class='viz-card-hed' style='margin-bottom:4px'>{hed}</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(style_chart(fig, h), width="stretch",
                        config={'displayModeBar': False})
        st.markdown(f"<div class='viz-dek'>{dek}</div>", unsafe_allow_html=True)

@st.cache_data
def img_b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def img_card(tag, tag_color, hed, path, caption, width_ratio=(1, 6, 1)):
    with st.container(border=True):
        st.markdown(f"""
        <span class='viz-card-tag' style='color:{tag_color}'>{tag}</span>
        <div class='viz-card-hed' style='margin-bottom:14px'>{hed}</div>
        """, unsafe_allow_html=True)
        left, mid, right = st.columns(list(width_ratio))
        with mid:
            st.markdown(f"<img class='dark-img' src='data:image/png;base64,{img_b64(path)}'>",
                        unsafe_allow_html=True)
        st.markdown(f"<div class='viz-dek'>{caption}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- data
ov      = q("SELECT COUNT(*) total, ROUND(AVG(is_churn)*100,2) churn, ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) rev_ret, ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) rev_ch FROM users").iloc[0]
per_day = q("SELECT is_churn, AVG(actual_amount_paid*1.0/payment_plan_days) per_day FROM users WHERE payment_plan_days > 0 GROUP BY is_churn").set_index("is_churn")["per_day"]
eng     = q("SELECT is_churn, AVG(completion_rate) completion, AVG(avg_secs_per_day)/60.0 mins_per_day FROM users GROUP BY is_churn ORDER BY is_churn")
cohort  = q("SELECT cohort, cohort_size, retained, retention_rate FROM cohort_retention WHERE cohort>='2015-01' ORDER BY cohort")
auto_df = q("SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew ON' ELSE 'Auto-renew OFF' END status, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE is_auto_renew IS NOT NULL GROUP BY is_auto_renew ORDER BY is_auto_renew DESC")
plan_df = q("SELECT payment_plan_days, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE payment_plan_days IN (7,30,90,180,365) GROUP BY payment_plan_days ORDER BY payment_plan_days")
reg_df  = q("SELECT registered_via, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE registered_via IS NOT NULL GROUP BY registered_via ORDER BY churn_pct DESC")
risk_df = q("SELECT risk_tier, COUNT(*) users, ROUND(AVG(churn_probability)*100,1) avg_prob, ROUND(SUM(churn_probability*plan_list_price),0) rev_at_risk FROM risk_scores GROUP BY risk_tier ORDER BY avg_prob DESC")
tier_agg = q("SELECT risk_tier, COUNT(*) n, AVG(churn_probability) p, AVG(plan_list_price) price FROM risk_scores GROUP BY risk_tier")
roi     = q("SELECT * FROM roi_summary LIMIT 1").iloc[0]

off_churn = float(auto_df.loc[auto_df.status == "Auto-renew OFF", "churn_pct"].iloc[0])
on_churn  = float(auto_df.loc[auto_df.status == "Auto-renew ON",  "churn_pct"].iloc[0])
gap_x     = off_churn / on_churn if on_churn else 0
n_scored  = int(risk_df["users"].sum())
n_high    = int(risk_df.loc[risk_df.risk_tier == "High Risk", "users"].sum())

@st.cache_data
def threshold_curve():
    r = q("SELECT churn_probability p, actual_churn y FROM risk_scores")
    p, y = r["p"].to_numpy(), r["y"].to_numpy()
    rows = []
    for t in np.round(np.arange(0.05, 0.96, 0.01), 2):
        pred = p >= t
        tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        prec = tp / (tp + fp) if tp + fp else 0
        rec  = tp / (tp + fn) if tp + fn else 0
        f1   = 2 * prec * rec / (prec + rec) if prec + rec else 0
        rows.append((t, prec, rec, f1))
    return pd.DataFrame(rows, columns=["threshold", "precision", "recall", "f1"])

# ---------------------------------------------------------------- hero
st.markdown(f"""
<div class='hero' style='background:{CARD};border:1px solid {BORDER};border-radius:16px;
            padding:44px 48px 40px;margin-bottom:28px'>
  <div class='eyebrow'>Portfolio Project &nbsp;·&nbsp; KKBox Music Streaming &nbsp;·&nbsp; {int(ov['total']):,} subscribers</div>
  <div class='display'>Churn here is a <em>payments</em> problem,<br>not an engagement problem.</div>
  <div class='lead'>
    People who left KKBox listened just as much as people who stayed. What separated them
    was how they paid: with auto-renew off, churn ran <b style='color:{WHITE}'>{gap_x:.0f}× higher</b>.
    This dashboard walks through the evidence, scores who is most likely to leave,
    and lets you test a retention campaign yourself.
  </div>
  <div style='margin:20px 0 28px'>
    <span class='pill'>Python</span><span class='pill'>SQL</span>
    <span class='pill'>XGBoost</span><span class='pill'>SHAP</span>
    <span class='pill'>Streamlit</span>
    <span class='pill' style='border-color:{GREEN};color:{GREEN}'>AUC 0.9876</span>
    <span class='pill' style='border-color:{ACCENT};color:{ACCENT}'>5-fold CV ±0.0003</span>
  </div>
  <div class='stat-row'>
    <div class='stat-item' style='border-color:{GREEN}'>
      <div class='stat-label'>Subscribers analysed</div>
      <div class='stat-value'>{int(ov['total']):,}</div>
    </div>
    <div class='stat-item' style='border-color:{MUTED}'>
      <div class='stat-label'>Overall churn</div>
      <div class='stat-value'>{ov['churn']}%</div>
    </div>
    <div class='stat-item' style='border-color:{RED}'>
      <div class='stat-label'>Churn · auto-renew off</div>
      <div class='stat-value' style='color:{RED}'>{off_churn:.1f}%</div>
    </div>
    <div class='stat-item' style='border-color:{GREEN}'>
      <div class='stat-label'>Churn · auto-renew on</div>
      <div class='stat-value' style='color:{GREEN}'>{on_churn:.1f}%</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Why they leave", "Retention over time", "Who to save",
    "Campaign simulator", "Model checks",
])

# ================================================================ TAB 1: drivers
with tab1:
    st.markdown(f"""
    <div class='section-hed'>The obvious guess was engagement. The data says otherwise.</div>
    <div class='section-dek'>
      If churn were an engagement problem, people would stop listening before they left.
      They don't. The strongest differences between churned and retained users are all about
      payments and subscription setup.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        labels = ["Retained", "Churned"]
        e = eng.set_index("is_churn")
        ef = make_subplots(rows=1, cols=2, subplot_titles=("Song completion rate", "Minutes listened per day"),
                           horizontal_spacing=0.18)
        ef.add_bar(x=labels, y=[e.loc[0, "completion"], e.loc[1, "completion"]],
                   marker_color=[GREEN, RED], text=[f"{v:.2f}" for v in e["completion"]],
                   textposition="outside", textfont=dict(color=WHITE), row=1, col=1,
                   hovertemplate="%{x}: %{y:.2f}<extra></extra>")
        ef.add_bar(x=labels, y=[e.loc[0, "mins_per_day"], e.loc[1, "mins_per_day"]],
                   marker_color=[GREEN, RED], text=[f"{v:.0f} min" for v in e["mins_per_day"]],
                   textposition="outside", textfont=dict(color=WHITE), row=1, col=2,
                   hovertemplate="%{x}: %{y:.0f} min<extra></extra>")
        ef.update_layout(showlegend=False, bargap=0.45)
        ef.update_yaxes(rangemode="tozero")
        ef.update_yaxes(range=[0, max(e["completion"]) * 1.25], row=1, col=1)
        ef.update_yaxes(range=[0, max(e["mins_per_day"]) * 1.25], row=1, col=2)
        chart_card("THE PROOF", BLUE,
            "Churned users listened just as much",
            "Completion rate and daily listening time are nearly identical for both groups. "
            "Whatever is making people leave, it isn't that they stopped using the product.",
            ef)

    with col2:
        auto_fig = px.bar(auto_df, x="status", y="churn_pct", color="status",
                    color_discrete_map={"Auto-renew ON": GREEN, "Auto-renew OFF": RED},
                    text=auto_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct": "Churn rate (%)", "status": ""})
        auto_fig.update_traces(textposition='outside',
                               textfont=dict(size=16, color=WHITE), width=0.45,
                               hovertemplate="%{x}: %{y}% churn<extra></extra>")
        auto_fig.update_layout(showlegend=False, yaxis_range=[0, off_churn * 1.25])
        chart_card("THE BIGGEST LEVER", RED,
            f"Auto-renew off: {gap_x:.0f}× the churn rate",
            "Same listening habits, very different outcomes. Users who have to actively renew "
            "churn far more, which makes auto-renew the most actionable lever in the data.",
            auto_fig)

    st.write("")
    col3, col4 = st.columns(2)
    with col3:
        plan_df['label'] = plan_df['payment_plan_days'].apply(
            lambda x: {7: "7 days", 30: "30 days", 90: "3 months",
                       180: "6 months", 365: "1 year"}.get(int(x), f"{int(x)}d"))
        plan_fig = px.bar(plan_df, x="label", y="churn_pct", color="churn_pct",
                    color_continuous_scale=[[0, GREEN], [0.5, AMBER], [1, RED]],
                    text=plan_df['churn_pct'].apply(lambda x: f"{x}%"),
                    labels={"churn_pct": "Churn rate (%)", "label": ""})
        plan_fig.update_traces(textposition='outside', textfont=dict(size=14, color=WHITE),
                               hovertemplate="%{x}: %{y}% churn<extra></extra>")
        plan_fig.update_layout(coloraxis_showscale=False)
        chart_card("PLAN STRUCTURE", AMBER,
            "Plan length changes who sticks around",
            "Churn varies sharply by plan length. Longer plans are paid upfront, so renewal "
            "becomes one big, deliberate decision instead of a routine monthly charge.",
            plan_fig)

    with col4:
        reg_df['ch'] = reg_df['registered_via'].apply(lambda x: f"Ch {int(x)}")
        reg_fig = px.bar(reg_df, x="ch", y="churn_pct", color="churn_pct",
                    color_continuous_scale=[[0, GREEN], [0.5, AMBER], [1, RED]],
                    text=reg_df['churn_pct'].apply(lambda x: f"{x:.1f}%"),
                    labels={"churn_pct": "Churn (%)", "ch": ""})
        reg_fig.update_traces(textposition='outside', textfont=dict(size=12, color=WHITE),
                              hovertemplate="%{x}: %{y:.1f}% churn<extra></extra>")
        reg_fig.update_layout(coloraxis_showscale=False)
        spread = reg_df['churn_pct'].max() / max(reg_df['churn_pct'].min(), 0.01)
        chart_card("ACQUISITION", BLUE,
            f"Sign-up channel matters: {spread:.0f}× gap between best and worst",
            "Channel IDs are anonymised sign-up pathways, and KKBox hasn't published the mapping. "
            "The difference in churn is still large and consistent.",
            reg_fig)

    st.write("")
    img_card("WHAT THE MODEL LEARNED", GREEN,
        "Payment and subscription features dominate; listening features barely register",
        ASSETS_PATH / "shap_beeswarm.png",
        "Each dot is one user. Pink means a high feature value, blue means low; dots to the right "
        "push the prediction towards churn. The top of the chart is expiry dates, pricing, cancellations "
        "and payment method. Listening behaviour sits near the bottom.",
        width_ratio=(1, 3, 1))

    ratio_total = ov['rev_ch'] / ov['rev_ret'] if ov['rev_ret'] else 0
    ratio_day   = per_day.get(1, 0) / per_day.get(0, 1) if per_day.get(0, 0) else 0
    if ratio_day < 1.5:
        rev_line = (f"Per day of subscription it's TWD {per_day.get(1,0):.1f} vs {per_day.get(0,0):.1f}, "
                    "so most of that gap comes from plan length, not from churners paying more for the same thing.")
    else:
        rev_line = (f"Even per day of subscription the gap holds (TWD {per_day.get(1,0):.1f} vs {per_day.get(0,0):.1f}), "
                    "so churners really are the higher-paying users.")
    st.markdown(f"""
    <div class='insight insight-amber'>
      <b>A number worth reading carefully:</b> churned users' last payment averaged
      TWD {ov['rev_ch']:,.0f} vs TWD {ov['rev_ret']:,.0f} for retained users ({ratio_total:.1f}×).
      {rev_line}
    </div>
    """, unsafe_allow_html=True)

# ================================================================ TAB 2: cohorts
with tab2:
    avg_r = cohort['retention_rate'].mean()
    best  = cohort.loc[cohort['retention_rate'].idxmax()]

    st.markdown(f"""
    <div class='section-hed'>Retention is stable over time</div>
    <div class='section-dek'>
      Each bar is one month of new sign-ups, showing the share of that cohort that didn't churn.
      Split into two panels so every cohort stays readable.
    </div>
    """, unsafe_allow_html=True)

    mid = len(cohort) // 2
    c1, c2 = st.columns(2)

    def cohort_fig(df_s):
        f = px.bar(df_s, x="retention_rate", y="cohort", orientation='h',
                   color="retention_rate",
                   color_continuous_scale=[[0, RED], [0.5, AMBER], [1, GREEN]],
                   text=df_s['retention_rate'].apply(lambda x: f"{x:.1f}%"),
                   labels={"retention_rate": "Retention (%)", "cohort": ""},
                   custom_data=["cohort_size"])
        f.update_traces(textposition='outside', textfont=dict(size=11, color=WHITE),
                        hovertemplate="%{y}: %{x:.1f}% retained<br>%{customdata[0]:,} users<extra></extra>")
        f.update_layout(coloraxis_showscale=False, xaxis_range=[80, 103],
                        yaxis={'categoryorder': 'category ascending'})
        return f

    with c1:
        chart_card("RECENT", MUTED, "Most recent cohorts",
                   "The later half of sign-up months.", cohort_fig(cohort.iloc[mid:]), 480)
    with c2:
        chart_card("EARLIER", MUTED, "Earlier cohorts",
                   "January 2015 to the midpoint.", cohort_fig(cohort.iloc[:mid]), 480)

    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Average retention", f"{avg_r:.1f}%")
    m2.metric("Best cohort", str(best['cohort']), f"{best['retention_rate']:.1f}%")
    m3.metric("Cohorts tracked", str(len(cohort)))

    st.markdown(f"""
    <div class='insight'>
      <b>So what?</b> Retention hasn't meaningfully declined across cohorts, so this isn't a
      story about the product getting worse. That points the investigation back to how people pay.
    </div>
    """, unsafe_allow_html=True)

# ================================================================ TAB 3: risk
with tab3:
    tier_c = {"High Risk": RED, "Medium Risk": AMBER, "Low Risk": GREEN}

    st.markdown(f"""
    <div class='section-hed'>Every scored user sorted into three tiers, with one clear priority</div>
    <div class='section-dek'>
      The model gives each of the {n_scored:,} users in the hold-out set a churn probability.
      High Risk users are the most likely to leave and carry the most revenue at stake,
      so they are where a retention budget should go first.
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    for col, (_, row) in zip([r1, r2, r3], risk_df.iterrows()):
        clr = tier_c.get(row['risk_tier'], MUTED)
        with col:
            st.markdown(f"""
            <div style='background:{CARD};border:1px solid {BORDER};
                        border-top:3px solid {clr};border-radius:14px;
                        padding:26px 28px;height:230px'>
              <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.14em;color:{clr};margin-bottom:14px'>
                {row['risk_tier']}
              </div>
              <div style='font-size:40px;font-weight:700;color:{WHITE};line-height:1'>
                {int(row['users']):,}
              </div>
              <div style='font-size:13px;color:{MUTED};margin-bottom:14px'>users</div>
              <div style='border-top:1px solid {BORDER};padding-top:12px'>
                <div style='font-size:13px;color:{BODY}'>
                  Avg churn probability
                  <span style='font-weight:700;color:{clr}'>&nbsp;{row['avg_prob']}%</span>
                </div>
                <div style='font-size:13px;color:{BODY};margin-top:6px'>
                  Revenue at risk
                  <span style='font-weight:700;color:{WHITE}'>&nbsp;TWD {row['rev_at_risk']:,.0f}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    rc1, rc2 = st.columns(2)
    tiers = risk_df['risk_tier'].tolist()
    clrs  = [tier_c.get(t, MUTED) for t in tiers]

    with rc1:
        f5 = go.Figure(go.Bar(
            x=tiers, y=risk_df['users'].tolist(), marker_color=clrs,
            text=[f"{v:,}" for v in risk_df['users'].tolist()],
            textposition='outside', textfont=dict(color=WHITE, size=13),
            hovertemplate="%{x}: %{y:,} users<extra></extra>"))
        f5.update_layout(yaxis_title="Users", showlegend=False)
        chart_card("DISTRIBUTION", GREEN, "Users per risk tier",
            "High Risk users are a small slice of the base.", f5)

    with rc2:
        f6 = go.Figure(go.Bar(
            x=tiers, y=risk_df['rev_at_risk'].tolist(), marker_color=clrs,
            text=[f"TWD {v:,.0f}" for v in risk_df['rev_at_risk'].tolist()],
            textposition='outside', textfont=dict(color=WHITE, size=12),
            hovertemplate="%{x}: TWD %{y:,.0f}<extra></extra>"))
        f6.update_layout(yaxis_title="TWD", showlegend=False)
        chart_card("IMPACT", AMBER, "Revenue at risk per tier",
            "...but they hold the largest share of revenue at stake.", f6)

    st.markdown(f"""
    <div class='insight'>
      <b>Where to act first:</b> the {n_high:,} High Risk users combine the highest churn probability
      with the most revenue at stake. Head to the <b>Campaign simulator</b> tab to see what
      a retention offer aimed at them would cost and return.
    </div>
    """, unsafe_allow_html=True)

    top_risk = q("""
        WITH ranked_risk AS (
            SELECT
                risk_tier,
                churn_probability,
                plan_list_price,
                ROUND(churn_probability * plan_list_price, 0) AS revenue_at_stake,
                ROW_NUMBER() OVER (
                    PARTITION BY risk_tier
                    ORDER BY churn_probability * plan_list_price DESC
                ) AS rank_in_tier
            FROM risk_scores
        )
        SELECT risk_tier, churn_probability, plan_list_price, revenue_at_stake, rank_in_tier
        FROM ranked_risk
        WHERE rank_in_tier <= 10
        ORDER BY risk_tier, rank_in_tier
    """)

    st.markdown(f"""
    <div class='section-hed' style='margin-top:28px'>Top 10 users to prioritise, per tier</div>
    <div class='section-dek'>
      Ranked within each tier by revenue at stake (churn probability × plan price).
      This is the actual intervention shortlist, not just the tier bucket.
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.dataframe(
            top_risk.style.format({
                'churn_probability': '{:.1%}',
                'plan_list_price': 'TWD {:.0f}',
                'revenue_at_stake': 'TWD {:.0f}'
            }),
            width="stretch", hide_index=True
        )

# ================================================================ TAB 4: simulator
with tab4:
    st.markdown(f"""
    <div class='eyebrow' style='color:{GREEN}'>Campaign simulator</div>
    <div class='section-hed' style='font-size:22px'>Would an auto-renew offer pay for itself?</div>
    <div class='section-dek'>
      The offer: a discount for anyone who switches auto-renew on. Pick who receives it,
      how generous it is, and how many would-be churners you expect to take it.
      Defaults match the original analysis: High Risk users, 10% off, 30% uptake.
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        cA, cB, cC = st.columns([1.3, 1, 1], gap="large")
        with cA:
            tiers_sel = st.multiselect("Who receives the offer",
                                       ["High Risk", "Medium Risk", "Low Risk"],
                                       default=["High Risk"])
        with cB:
            disc = st.slider("Discount for switching auto-renew on", 5, 30, 10, step=1, format="%d%%")
        with cC:
            conv = st.slider("Would-be churners who accept", 5, 60, 30, step=5, format="%d%%")

    sel = tier_agg[tier_agg.risk_tier.isin(tiers_sel)]
    if sel.empty:
        st.info("Pick at least one tier to run the numbers.")
    else:
        n_t        = int(sel.n.sum())
        cost       = float((sel.n * sel.price).sum() * disc / 100)
        users_kept = float((sel.n * sel.p).sum() * conv / 100)
        saved      = float((sel.n * sel.p * sel.price).sum() * conv / 100)
        roi_x      = saved / cost if cost else 0
        who        = " + ".join(t.replace(" Risk", "") for t in tiers_sel) + " Risk"
        verdict_c  = GREEN if roi_x >= 1 else RED
        verdict    = (f"That's <span style='color:{GREEN}'>{roi_x:.1f}× back</span> on every TWD spent."
                      if roi_x >= 1 else
                      f"That <span style='color:{RED}'>loses money</span>: only {roi_x:.2f}× back per TWD spent.")

        st.markdown(f"""
        <div class='hero' style='background:{CARD};border:1px solid {BORDER};
                    border-top:3px solid {verdict_c};border-radius:14px;
                    padding:30px 36px;margin:18px 0 20px'>
          <div class='sim-hed'>
            Offering <span style='color:{AMBER}'>{disc}% off</span> to
            <span style='color:{WHITE}'>{n_t:,} {who}</span> users costs
            <span style='color:{AMBER}'>TWD {cost:,.0f}</span> and keeps an estimated
            <span style='color:{GREEN}'>{users_kept:,.0f} subscribers</span>,
            protecting <span style='color:{GREEN}'>TWD {saved:,.0f}</span>. {verdict}
          </div>
        </div>
        """, unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Users targeted", f"{n_t:,}")
        s2.metric("Campaign cost", f"TWD {cost:,.0f}")
        s3.metric("Revenue protected", f"TWD {saved:,.0f}")
        s4.metric("Return on spend", f"{roi_x:.1f}×",
                  delta="pays for itself" if roi_x >= 1 else "loses money",
                  delta_color="normal" if roi_x >= 1 else "inverse")

        st.write("")
        order = ["High Risk", "Medium Risk", "Low Risk"]
        ta = tier_agg.set_index("risk_tier").reindex(order).dropna()
        roi_by_tier = ta["p"] * (conv / 100) / (disc / 100)
        rf = go.Figure(go.Bar(
            x=roi_by_tier.index.tolist(), y=roi_by_tier.values,
            marker_color=[RED if t in tiers_sel else BORDER for t in roi_by_tier.index],
            text=[f"{v:.1f}×" if v >= 0.1 else f"{v:.2f}×" for v in roi_by_tier.values],
            textposition="outside", textfont=dict(color=WHITE, size=13),
            hovertemplate="%{x}: %{y:.2f}× return<extra></extra>"))
        rf.add_hline(y=1, line_dash="dash", line_color=MUTED,
                     annotation_text="break-even", annotation_font_color=MUTED)
        rf.update_layout(showlegend=False, yaxis_title="Return per TWD spent",
                         yaxis_range=[0, max(roi_by_tier.max() * 1.25, 1.3)])
        chart_card("WHY TARGETING MATTERS", GREEN,
            "Return per tier at these settings",
            "Price cancels out, so each tier's return is simply its churn probability × uptake ÷ discount. "
            "The same offer that pays off for High Risk users loses money on Low Risk ones, because most of "
            "them were never going to leave. Highlighted bars are the tiers you selected.",
            rf, 320)

        st.markdown(f"""
        <div class='sim-note' style='margin-top:14px'>
          Assumptions: everyone targeted gets the discount on one plan period; uptake applies to users
          who would otherwise churn; saved revenue counts one plan period per retained user.
          Uptake is the biggest unknown here. A real rollout would test it on a small holdout group first,
          with churn among non-targeted users as the guardrail metric.
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    recs = [
        {"num": "01", "color": GREEN, "label": "HIGHEST IMPACT",
         "title": "Give users a reason to turn auto-renew on",
         "finding": f"Users with auto-renew off churn at {gap_x:.0f}× the rate of those with it on, despite listening just as much. They haven't stopped valuing the product; they just haven't committed to renewing.",
         "action": f"Offer a discount for switching auto-renew on, starting with the {n_high:,} High Risk users. At 10% off and 30% uptake, the model estimates a {roi['roi_ratio']}× return. Test the uptake assumption before scaling."},
        {"num": "02", "color": AMBER, "label": "RENEWAL MOMENT",
         "title": "Treat plan expiry as a moment to win users back",
         "finding": "Churn varies sharply by plan length, and expiry timing is one of the model's strongest signals. For users paying upfront, renewal is a single, deliberate decision rather than a routine charge.",
         "action": "Test a nudge shortly before long plans expire: offer auto-renew or a monthly option instead of letting the plan simply run out."},
        {"num": "03", "color": BLUE, "label": "ACQUISITION QUALITY",
         "title": "Audit acquisition channel spend",
         "finding": "The worst sign-up channel produces users who churn many times more often than the best one, and channel ranks among the model's meaningful predictors.",
         "action": "Map the anonymised channel IDs to real channels, shift spend away from high-churn ones, and reinvest where users stay, even if upfront volume is lower."},
    ]

    for rec in recs:
        st.markdown(f"""
        <div style='background:{CARD};border:1px solid {BORDER};
                    border-left:4px solid {rec["color"]};
                    border-radius:0 14px 14px 0;
                    padding:26px 30px;margin-bottom:14px'>
          <div style='display:flex;align-items:baseline;gap:18px;margin-bottom:14px'>
            <span style='font-size:26px;font-weight:700;
                         color:{rec["color"]};opacity:0.35'>{rec["num"]}</span>
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

# ================================================================ TAB 5: model
with tab5:
    tc = threshold_curve()
    best_row = tc.loc[tc.f1.idxmax()]
    f1_default = float(tc.loc[(tc.threshold - 0.5).abs().idxmin(), "f1"])

    st.markdown(f"""
    <div style='background:{CARD};border:1px solid {BORDER};border-radius:14px;
                padding:28px 32px;margin-bottom:32px'>
      <div class='eyebrow'>Model performance summary</div>
      <div class='stat-row' style='margin-top:16px'>
        <div class='stat-item' style='border-color:{GREEN}'>
          <div class='stat-label'>Hold-out AUC</div>
          <div class='stat-value' style='color:{GREEN}'>0.9876</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>on unseen test data</div>
        </div>
        <div class='stat-item' style='border-color:{GREEN}'>
          <div class='stat-label'>5-fold CV mean</div>
          <div class='stat-value' style='color:{GREEN}'>0.9875</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>no sign of overfitting</div>
        </div>
        <div class='stat-item' style='border-color:{BLUE}'>
          <div class='stat-label'>CV std deviation</div>
          <div class='stat-value'>±0.0003</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>very stable across folds</div>
        </div>
        <div class='stat-item' style='border-color:{AMBER}'>
          <div class='stat-label'>Best F1 score</div>
          <div class='stat-value'>{best_row.f1:.3f}</div>
          <div style='font-size:12px;color:{BODY};margin-top:4px'>at threshold {best_row.threshold:.2f}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2)
    with mv1:
        mc = go.Figure(go.Bar(
            x=["Logistic Regression (baseline)", "XGBoost"], y=[0.9028, 0.9876],
            marker_color=[MUTED, GREEN], width=0.45,
            text=["0.9028", "0.9876"], textposition="outside",
            textfont=dict(color=WHITE, size=14),
            hovertemplate="%{x}: AUC %{y:.4f}<extra></extra>"))
        mc.add_hline(y=0.5, line_dash="dot", line_color=RED,
                     annotation_text="random guessing", annotation_font_color=RED)
        mc.update_layout(yaxis_title="ROC-AUC", yaxis_range=[0.4, 1.05], showlegend=False)
        chart_card("BASELINE COMPARISON", BLUE,
            "XGBoost beats the baseline by +0.085 AUC",
            "A simple linear model already does well (0.9028). The jump to 0.9876 shows there are "
            "non-linear patterns in subscription behaviour that justify the more complex model.",
            mc)
    with mv2:
        folds = [0.9873, 0.9875, 0.9873, 0.9871, 0.9880]
        cvf = go.Figure(go.Bar(
            x=[f"Fold {i}" for i in range(1, 6)], y=folds,
            marker_color=[GREEN if s >= np.mean(folds) else AMBER for s in folds], width=0.45,
            text=[f"{s:.4f}" for s in folds], textposition="outside",
            textfont=dict(color=WHITE, size=12),
            hovertemplate="%{x}: AUC %{y:.4f}<extra></extra>"))
        cvf.add_hline(y=float(np.mean(folds)), line_dash="dash", line_color=MUTED,
                      annotation_text=f"mean {np.mean(folds):.4f}", annotation_font_color=MUTED)
        cvf.update_layout(yaxis_title="ROC-AUC (zoomed)", yaxis_range=[0.985, 0.9895], showlegend=False)
        chart_card("CROSS-VALIDATION", GREEN,
            "The score holds across all 5 folds",
            "Every fold lands between 0.9871 and 0.9880. The axis is zoomed in to make the "
            "differences visible at all; this isn't a lucky train/test split.",
            cvf)

    st.write("")
    mv3, mv4 = st.columns(2)
    with mv3:
        th = go.Figure()
        th.add_scatter(x=tc.threshold, y=tc.f1, mode="lines", name="F1",
                       line=dict(color=ACCENT, width=3),
                       hovertemplate="threshold %{x:.2f}: F1 %{y:.3f}<extra></extra>")
        th.add_scatter(x=tc.threshold, y=tc.precision, mode="lines", name="Precision",
                       line=dict(color=BLUE, width=1.5, dash="dot"),
                       hovertemplate="threshold %{x:.2f}: precision %{y:.3f}<extra></extra>")
        th.add_scatter(x=tc.threshold, y=tc.recall, mode="lines", name="Recall",
                       line=dict(color=AMBER, width=1.5, dash="dot"),
                       hovertemplate="threshold %{x:.2f}: recall %{y:.3f}<extra></extra>")
        th.add_vline(x=0.5, line_dash="dash", line_color=MUTED,
                     annotation_text="default 0.5", annotation_font_color=MUTED)
        th.add_vline(x=float(best_row.threshold), line_dash="dash", line_color=GREEN,
                     annotation_text=f"best {best_row.threshold:.2f}", annotation_font_color=GREEN,
                     annotation_position="top left")
        th.update_layout(xaxis_title="Classification threshold", yaxis_range=[0, 1.05],
                         legend=dict(orientation="h", y=-0.25))
        chart_card("THRESHOLD TUNING", AMBER,
            "The default threshold leaves performance on the table",
            f"At 0.5, F1 is {f1_default:.3f}. Raising the threshold to {best_row.threshold:.2f} "
            f"lifts it to {best_row.f1:.3f} by cutting false alarms while still catching most churners. "
            "Recomputed live from the hold-out predictions.",
            th)
    with mv4:
        img_card("DEEP DIVE", RED,
            "How auto-renew moves individual predictions",
            ASSETS_PATH / "shap_dependence_autorenew.png",
            "Auto-renew is binary: 0 is off, 1 is on. With it off, the model consistently pushes "
            "churn probability up, which is why it's the most actionable single lever.")

# ---------------------------------------------------------------- footer
st.divider()
st.markdown(f"""
<p style='font-size:12px;color:{MUTED};text-align:center;line-height:2.2'>
WSDM KKBox Churn Prediction Dataset &nbsp;·&nbsp;
XGBoost AUC 0.9876 · 5-fold CV 0.9875 ±0.0003 &nbsp;·&nbsp;
Built by Akanksha Nayak
</p>
""", unsafe_allow_html=True)
