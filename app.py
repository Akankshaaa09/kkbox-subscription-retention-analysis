# ============================================================
# KKBox Subscription Retention & Churn Analysis
# Streamlit Dashboard, v3 (light editorial redesign)
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
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------- palette
# Monochrome, plus one accent that always means "churn / risk / loses money".
PAGE    = "#EFEFEC"
CARD    = "#FFFFFF"
INK     = "#0E0E0E"
BODY    = "#4A4A47"
MUTED   = "#8A8A85"
LINE    = "#E3E3DF"
FAINT   = "#F4F4F1"
GREY    = "#C9C9C4"
ACCENT  = "#FF4A1C"
ACCENT_SOFT = "#FFE4DB"

CHART_H = 340

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"], .stApp, .stMarkdown, button, input {{
      font-family: 'Inter', sans-serif !important;
      color: {INK};
  }}
  .stApp {{ background: {PAGE}; }}
  .block-container {{ padding-top: 2.2rem !important; max-width: 1240px; }}

  /* ---------- chrome ---------- */
  .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"], footer {{ display: none !important; }}
  header[data-testid="stHeader"] {{ background: transparent !important; }}

  /* ---------- motion ---------- */
  @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes spin   {{ to {{ transform: rotate(360deg); }} }}
  @keyframes pulse  {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
  .fade {{ animation: fadeUp .7s ease both; }}
  .fade-2 {{ animation: fadeUp .7s .12s ease both; }}
  .fade-3 {{ animation: fadeUp .7s .24s ease both; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ transition: transform .2s ease, box-shadow .2s ease; }}
  div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ transform: translateY(-2px); box-shadow: 0 14px 34px rgba(0,0,0,.06); }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}

  /* ---------- sidebar nav ---------- */
  [data-testid="stSidebar"] {{ background: {CARD}; border-right: 1px solid {LINE}; }}
  [data-testid="stSidebar"] [role="radiogroup"] {{ gap: 4px; }}
  [data-testid="stSidebar"] [role="radiogroup"] label {{
      padding: 10px 14px; border-radius: 999px; margin: 0; width: 100%;
      transition: background .15s ease;
  }}
  [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display: none; }}
  [data-testid="stSidebar"] [role="radiogroup"] label p {{ font-size: 14px; font-weight: 500; color: {BODY}; }}
  [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: {FAINT}; }}
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background: {INK}; }}
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{ color: {CARD}; }}

  /* ---------- buttons ---------- */
  .stButton button {{
      border-radius: 999px; font-weight: 600; font-size: 14px;
      padding: 10px 22px; transition: transform .15s ease, background .15s ease;
  }}
  .stButton button[kind="primary"] {{ background: {INK}; color: {CARD}; border: 1px solid {INK}; }}
  .stButton button[kind="primary"]:hover {{ background: #2A2A2A; transform: translateX(2px); }}
  .stButton button[kind="secondary"] {{ background: {CARD}; color: {INK}; border: 1px solid {LINE}; }}
  .stButton button[kind="secondary"]:hover {{ border-color: {INK}; color: {INK}; }}

  /* ---------- cards ---------- */
  div[data-testid="stVerticalBlockBorderWrapper"] > div {{
      background: {CARD} !important; border: 1px solid {LINE} !important;
      border-radius: 20px !important; padding: 22px 24px !important;
  }}
  div[data-testid="stMetric"] {{
      background: {CARD}; border: 1px solid {LINE}; border-radius: 16px; padding: 20px 22px;
  }}
  div[data-testid="stMetric"] label p {{
      font-family: 'JetBrains Mono', monospace !important; color: {MUTED} !important;
      font-size: 11px !important; text-transform: uppercase; letter-spacing: .08em;
  }}
  div[data-testid="stMetricValue"] {{
      font-family: 'Inter Tight', sans-serif !important; color: {INK} !important;
      font-size: 30px !important; font-weight: 700 !important;
  }}
  hr {{ border-color: {LINE} !important; margin: 36px 0 !important; }}

  /* ---------- type ---------- */
  .mono  {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .08em;
            text-transform: uppercase; color: {MUTED}; }}
  .tag   {{ display: inline-flex; align-items: center; gap: 8px; border: 1px solid {LINE};
            background: {CARD}; border-radius: 999px; padding: 6px 12px; }}
  .dot   {{ width: 7px; height: 7px; border-radius: 50%; background: {ACCENT}; display: inline-block; }}
  .mega  {{ font-family: 'Inter Tight', sans-serif; font-weight: 800; color: {INK};
            font-size: clamp(3rem, 6.2vw, 5.4rem); line-height: .95; letter-spacing: -.04em; margin: 18px 0 20px; }}
  .lead  {{ font-size: 15.5px; color: {BODY}; line-height: 1.75; max-width: 460px; }}
  .page-title {{ font-family: 'Inter Tight', sans-serif; font-weight: 800; font-size: clamp(2.2rem, 4.2vw, 3.4rem);
                 line-height: 1; letter-spacing: -.035em; color: {INK}; margin: 10px 0 14px; }}
  .page-dek {{ font-size: 15px; color: {BODY}; line-height: 1.75; max-width: 760px; margin-bottom: 30px; }}
  .card-tag {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .08em;
               text-transform: uppercase; margin-bottom: 8px; display: block; }}
  .card-hed {{ font-family: 'Inter Tight', sans-serif; font-size: 19px; font-weight: 700; color: {INK};
               line-height: 1.3; letter-spacing: -.01em; }}
  .card-dek {{ font-size: 13.5px; color: {BODY}; line-height: 1.7; padding-top: 14px; margin-top: 6px;
               border-top: 1px solid {LINE}; }}
  .fig-img  {{ width: 100%; border-radius: 10px; }}
  .note {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 16px; padding: 18px 22px;
           margin: 22px 0; font-size: 14px; color: {BODY}; line-height: 1.8; }}
  .note b {{ color: {INK}; }}
  .note-accent {{ background: {ACCENT_SOFT}; border-color: #FFC9B8; }}
  .accent {{ color: {ACCENT}; }}

  /* ---------- chapter list (overview) ---------- */
  .chap-num  {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {MUTED}; padding-top: 6px; }}
  .chap-eye  {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MUTED};
                text-transform: uppercase; letter-spacing: .08em; }}
  .chap-hed  {{ font-family: 'Inter Tight', sans-serif; font-size: 22px; font-weight: 600; color: {INK};
                letter-spacing: -.015em; line-height: 1.3; }}
  .rule      {{ border-top: 1px solid {LINE}; margin: 14px 0; }}

  /* ---------- stat cards ---------- */
  .stat-card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 20px; padding: 22px 26px;
                display: flex; gap: 34px; flex-wrap: wrap; }}
  .stat-num  {{ font-family: 'Inter Tight', sans-serif; font-weight: 800; font-size: 34px; color: {INK};
                letter-spacing: -.03em; line-height: 1; }}
  .stat-lbl  {{ font-size: 12.5px; color: {MUTED}; margin-top: 6px; line-height: 1.4; }}
  .grid4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
  @media (max-width: 800px) {{ .grid4 {{ grid-template-columns: repeat(2, 1fr); }} }}
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
        height=h, title=dict(text=""),
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(color=BODY, family="Inter", size=12),
        margin=dict(t=30, b=8, l=8, r=8),
        barcornerradius=8,
        legend=dict(bgcolor=CARD, font=dict(color=BODY, size=12)),
        hoverlabel=dict(bgcolor=INK, bordercolor=INK, font=dict(color=CARD, family="Inter")),
    )
    fig.update_xaxes(gridcolor=FAINT, linecolor=LINE, tickcolor=LINE, zeroline=False,
                     tickfont=dict(color=BODY, size=11), title_font=dict(color=MUTED, size=11))
    fig.update_yaxes(gridcolor=FAINT, linecolor=LINE, tickcolor=LINE, zeroline=False,
                     tickfont=dict(color=MUTED, size=11), title_font=dict(color=MUTED, size=11))
    fig.update_annotations(font=dict(color=BODY, size=12, family="Inter"))
    return fig

def chart_card(tag, hed, dek, fig, h=CHART_H, tag_color=MUTED):
    with st.container(border=True):
        st.markdown(f"<span class='card-tag' style='color:{tag_color}'>{tag}</span>"
                    f"<div class='card-hed' style='margin-bottom:4px'>{hed}</div>", unsafe_allow_html=True)
        st.plotly_chart(style_chart(fig, h), width="stretch", config={'displayModeBar': False})
        st.markdown(f"<div class='card-dek'>{dek}</div>", unsafe_allow_html=True)

@st.cache_data
def img_b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def img_card(tag, hed, path, caption, width_ratio=(1, 6, 1)):
    with st.container(border=True):
        st.markdown(f"<span class='card-tag'>{tag}</span>"
                    f"<div class='card-hed' style='margin-bottom:14px'>{hed}</div>", unsafe_allow_html=True)
        _, mid, _ = st.columns(list(width_ratio))
        with mid:
            st.markdown(f"<img class='fig-img' src='data:image/png;base64,{img_b64(path)}'>",
                        unsafe_allow_html=True)
        st.markdown(f"<div class='card-dek'>{caption}</div>", unsafe_allow_html=True)

def page_header(num, name, title, dek):
    st.markdown(f"""
    <div class='fade'>
      <span class='mono'>{num} / {name}</span>
      <div class='page-title'>{title}</div>
      <div class='page-dek'>{dek}</div>
    </div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- data
ov      = q("SELECT COUNT(*) total, ROUND(AVG(is_churn)*100,2) churn, ROUND(AVG(CASE WHEN is_churn=0 THEN actual_amount_paid END),2) rev_ret, ROUND(AVG(CASE WHEN is_churn=1 THEN actual_amount_paid END),2) rev_ch FROM users").iloc[0]
per_day = q("SELECT is_churn, AVG(actual_amount_paid*1.0/payment_plan_days) per_day FROM users WHERE payment_plan_days > 0 GROUP BY is_churn").set_index("is_churn")["per_day"]
eng     = q("SELECT is_churn, AVG(completion_rate) completion, AVG(avg_secs_per_day)/60.0 mins_per_day FROM users GROUP BY is_churn ORDER BY is_churn")
cohort  = q("SELECT cohort, cohort_size, retained, retention_rate FROM cohort_retention WHERE cohort>='2015-01' ORDER BY cohort")
auto_df = q("SELECT CASE WHEN is_auto_renew=1 THEN 'Auto-renew on' ELSE 'Auto-renew off' END status, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE is_auto_renew IS NOT NULL GROUP BY is_auto_renew ORDER BY is_auto_renew")
plan_df = q("SELECT payment_plan_days, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE payment_plan_days IN (7,30,90,180,365) GROUP BY payment_plan_days ORDER BY payment_plan_days")
reg_df  = q("SELECT registered_via, COUNT(*) users, ROUND(AVG(is_churn)*100,2) churn_pct FROM users WHERE registered_via IS NOT NULL GROUP BY registered_via ORDER BY churn_pct DESC")
risk_df = q("SELECT risk_tier, COUNT(*) users, ROUND(AVG(churn_probability)*100,1) avg_prob, ROUND(SUM(churn_probability*plan_list_price),0) rev_at_risk FROM risk_scores GROUP BY risk_tier ORDER BY avg_prob DESC")
tier_agg = q("SELECT risk_tier, COUNT(*) n, AVG(churn_probability) p, AVG(plan_list_price) price FROM risk_scores GROUP BY risk_tier")
roi     = q("SELECT * FROM roi_summary LIMIT 1").iloc[0]

total     = int(ov["total"])
off_churn = float(auto_df.loc[auto_df.status == "Auto-renew off", "churn_pct"].iloc[0])
on_churn  = float(auto_df.loc[auto_df.status == "Auto-renew on",  "churn_pct"].iloc[0])
gap_x     = off_churn / on_churn if on_churn else 0
n_scored  = int(risk_df["users"].sum())
n_high    = int(risk_df.loc[risk_df.risk_tier == "High Risk", "users"].sum())
TIER_C    = {"High Risk": ACCENT, "Medium Risk": MUTED, "Low Risk": GREY}

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

@st.cache_data
def dot_ring(n_dots, n_churn):
    """One dot per 1,000 subscribers, scattered in a slowly turning ring. Churned dots in the accent."""
    rng = np.random.default_rng(7)
    ang = rng.uniform(0, 2 * np.pi, n_dots)
    rad = 150 + rng.normal(0, 22, n_dots) + rng.choice([0, 0, 0, 0, 38, -44], n_dots) * rng.random(n_dots)
    x, y = 250 + rad * np.cos(ang), 250 + rad * np.sin(ang)
    size = rng.choice([1.3, 1.8, 2.3, 3.0, 3.8], n_dots, p=[.34, .28, .2, .12, .06])
    opac = rng.uniform(.25, .95, n_dots)
    churn_idx = set(rng.choice(n_dots, n_churn, replace=False).tolist())
    grid = "".join(f"<line x1='{v}' y1='0' x2='{v}' y2='500'/><line x1='0' y1='{v}' x2='500' y2='{v}'/>"
                   for v in range(50, 500, 50))
    marks = "".join(f"<path d='M{a-6},{b}h12M{a},{b-6}v12'/>" for a, b in
                    [(50, 50), (450, 50), (50, 450), (450, 450), (250, 250)])
    ink, acc = [], []
    for i in range(n_dots):
        if i in churn_idx:
            acc.append(f"<circle class='c c{i % 4}' cx='{x[i]:.1f}' cy='{y[i]:.1f}' r='{max(size[i], 2.6):.1f}'/>")
        else:
            ink.append(f"<circle cx='{x[i]:.1f}' cy='{y[i]:.1f}' r='{size[i]:.1f}' opacity='{opac[i]:.2f}'/>")
    return f"""
    <svg viewBox='0 0 500 500' width='100%' role='img' aria-label='{n_dots} dots, {n_churn} highlighted as churned'>
      <style>
        .ring {{ transform-origin: 250px 250px; animation: spin 140s linear infinite; }}
        .c {{ animation: pulse 3.2s ease-in-out infinite; }}
        .c1 {{ animation-delay: .8s; }} .c2 {{ animation-delay: 1.6s; }} .c3 {{ animation-delay: 2.4s; }}
      </style>
      <g stroke='#ECECE8' stroke-width='1'>{grid}</g>
      <g stroke='{GREY}' stroke-width='1.2'>{marks}</g>
      <g class='ring'>
        <g fill='{INK}'>{''.join(ink)}</g>
        <g fill='{ACCENT}'>{''.join(acc)}</g>
      </g>
    </svg>"""

# ---------------------------------------------------------------- navigation
NAV = ["00  Overview", "01  Why they leave", "02  Retention", "03  Who to save",
       "04  Simulator", "05  Model checks"]

def goto(page):
    st.session_state["nav"] = page

with st.sidebar:
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin:6px 0 26px'>
      <svg width='26' height='26' viewBox='0 0 26 26' aria-hidden='true'>
        <g stroke='{INK}' stroke-width='2' stroke-linecap='round'>
          {''.join(f"<line x1='13' y1='13' x2='{13+10*np.cos(a):.1f}' y2='{13+10*np.sin(a):.1f}'/>" for a in np.linspace(0, 2*np.pi, 12, endpoint=False))}
        </g><circle cx='13' cy='13' r='3' fill='{ACCENT}'/>
      </svg>
      <div style='font-family:Inter Tight;font-weight:700;font-size:16px;color:{INK}'>KKBox Churn</div>
    </div>
    """, unsafe_allow_html=True)
    page = st.radio("Navigate", NAV, key="nav", label_visibility="collapsed")
    st.markdown(f"""
    <div style='margin-top:34px;background:{FAINT};border-radius:16px;padding:16px 16px 14px'>
      <div class='mono' style='margin-bottom:8px'>Built with</div>
      <div style='font-size:13px;color:{BODY};line-height:1.7'>Python · SQL · XGBoost · SHAP · Streamlit</div>
      <div class='rule'></div>
      <div style='font-size:13px;color:{BODY};line-height:1.8'>
        Built by <b style='color:{INK}'>Akanksha Nayak</b><br>
        <a href='https://github.com/Akankshaaa09/kkbox-subscription-retention-analysis' target='_blank' style='color:{INK}'>GitHub repo ↗</a><br>
        <a href='https://akankshaaa09.github.io' target='_blank' style='color:{INK}'>Portfolio ↗</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ================================================================ 00 OVERVIEW
if page == NAV[0]:
    n_dots  = round(total / 1000)
    n_churn = round(total * float(ov["churn"]) / 100 / 1000)

    with st.container(border=True):
        left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown(f"<div class='fade'>{dot_ring(n_dots, n_churn)}</div>", unsafe_allow_html=True)
        with right:
            st.markdown(f"""
            <div class='fade-2'>
              <span class='tag mono'><span class='dot'></span>Subscription intelligence</span>
              <div class='mega'>Payments.<br>Not plays.</div>
              <div class='lead'>
                Across {total:,} KKBox subscribers, the people who left listened just as much as
                the people who stayed. What separated them was how they paid: with auto-renew off,
                churn ran <b style='color:{INK}'>{gap_x:.0f}× higher</b>.
              </div>
            </div>""", unsafe_allow_html=True)
            st.write("")
            st.button("Try the campaign simulator  →", type="primary", on_click=goto, args=(NAV[4],))

        st.write("")
        b1, b2 = st.columns([1, 1.35], gap="medium")
        with b1:
            st.markdown(f"""
            <div class='fade-3' style='background:{FAINT};border-radius:20px;padding:22px 24px;height:100%'>
              <div style='font-family:Inter Tight;font-weight:700;font-size:17px;color:{INK};margin-bottom:6px'>
                Turning {total // 1000}K subscriptions into a retention plan
              </div>
              <div style='font-size:13px;color:{BODY};line-height:1.7'>
                Each dot is 1,000 subscribers. The <span class='accent'><b>{n_churn} orange ones</b></span> left.
              </div>
            </div>""", unsafe_allow_html=True)
        with b2:
            st.markdown(f"""
            <div class='stat-card fade-3'>
              <div><div class='stat-num'>{total // 1000}K</div><div class='stat-lbl'>Subscribers<br>analysed</div></div>
              <div><div class='stat-num accent'>{gap_x:.0f}×</div><div class='stat-lbl'>Churn gap, auto-renew<br>off vs on</div></div>
              <div><div class='stat-num'>0.988</div><div class='stat-lbl'>Model AUC on<br>unseen data</div></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div><span class='mono'>The story in five chapters</span>"
                "<div class='rule' style='margin-top:12px'></div>", unsafe_allow_html=True)
    chapters = [
        (NAV[1], "Why they leave", "Listening didn't predict churn. Payments did."),
        (NAV[2], "Retention", "Cohorts stay steady, so the product isn't getting worse."),
        (NAV[3], "Who to save", f"{n_high:,} users carry most of the revenue at risk."),
        (NAV[4], "Simulator", "Test whether an auto-renew offer pays for itself."),
        (NAV[5], "Model checks", "AUC 0.9876, stable across five folds, threshold tuned."),
    ]
    for nav_key, eye, hed in chapters:
        c0, c1, c2 = st.columns([0.5, 6, 1.3], vertical_alignment="center")
        c0.markdown(f"<div class='chap-num'>{nav_key[:2]}</div>", unsafe_allow_html=True)
        c1.markdown(f"<div class='chap-eye'>{eye}</div><div class='chap-hed'>{hed}</div>", unsafe_allow_html=True)
        c2.button("Open  →", key=f"open_{eye}", on_click=goto, args=(nav_key,), width="stretch")
        st.markdown("<div class='rule'></div>", unsafe_allow_html=True)

# ================================================================ 01 WHY THEY LEAVE
elif page == NAV[1]:
    page_header("01", "Why they leave", "The obvious guess was engagement.<br>The data disagrees.",
        "If churn were an engagement problem, people would stop listening before they left. They don't. "
        "The biggest differences between churned and retained users are about payments and subscription setup.")

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        labels = ["Retained", "Churned"]
        e = eng.set_index("is_churn")
        ef = make_subplots(rows=1, cols=2, subplot_titles=("Song completion rate", "Minutes listened per day"),
                           horizontal_spacing=0.18)
        ef.add_bar(x=labels, y=[e.loc[0, "completion"], e.loc[1, "completion"]],
                   marker_color=[INK, ACCENT], text=[f"{v:.2f}" for v in e["completion"]],
                   textposition="outside", textfont=dict(color=INK), row=1, col=1,
                   hovertemplate="%{x}: %{y:.2f}<extra></extra>")
        ef.add_bar(x=labels, y=[e.loc[0, "mins_per_day"], e.loc[1, "mins_per_day"]],
                   marker_color=[INK, ACCENT], text=[f"{v:.0f} min" for v in e["mins_per_day"]],
                   textposition="outside", textfont=dict(color=INK), row=1, col=2,
                   hovertemplate="%{x}: %{y:.0f} min<extra></extra>")
        ef.update_layout(showlegend=False, bargap=0.45)
        ef.update_yaxes(range=[0, max(e["completion"]) * 1.25], row=1, col=1)
        ef.update_yaxes(range=[0, max(e["mins_per_day"]) * 1.25], row=1, col=2)
        chart_card("The proof", "Churned users listened just as much",
            "Completion rate and daily listening time are nearly identical for both groups. "
            "Whatever is making people leave, it isn't that they stopped using the product.", ef)

    with col2:
        auto_fig = go.Figure(go.Bar(
            x=auto_df["status"], y=auto_df["churn_pct"],
            marker_color=[INK if s == "Auto-renew on" else ACCENT for s in auto_df["status"]],
            text=auto_df["churn_pct"].apply(lambda x: f"{x}%"), width=0.45,
            textposition="outside", textfont=dict(size=16, color=INK),
            hovertemplate="%{x}: %{y}% churn<extra></extra>"))
        auto_fig.update_layout(showlegend=False, yaxis_range=[0, off_churn * 1.25], yaxis_title="Churn rate (%)")
        chart_card("The biggest lever", f"Auto-renew off: {gap_x:.0f}× the churn rate",
            "Same listening habits, very different outcomes. Users who have to actively renew churn far more, "
            "which makes auto-renew the most actionable lever in the data.", auto_fig, tag_color=ACCENT)

    st.write("")
    col3, col4 = st.columns(2, gap="medium")
    ramp = [[0, GREY], [1, ACCENT]]
    with col3:
        plan_df["label"] = plan_df["payment_plan_days"].apply(
            lambda x: {7: "7 days", 30: "30 days", 90: "3 months", 180: "6 months", 365: "1 year"}.get(int(x), f"{int(x)}d"))
        plan_fig = px.bar(plan_df, x="label", y="churn_pct", color="churn_pct", color_continuous_scale=ramp,
                          text=plan_df["churn_pct"].apply(lambda x: f"{x}%"),
                          labels={"churn_pct": "Churn rate (%)", "label": ""})
        plan_fig.update_traces(textposition="outside", textfont=dict(size=13, color=INK),
                               hovertemplate="%{x}: %{y}% churn<extra></extra>")
        plan_fig.update_layout(coloraxis_showscale=False)
        chart_card("Plan structure", "Plan length changes who sticks around",
            "Churn varies sharply by plan length. Longer plans are paid upfront, so renewal becomes one big, "
            "deliberate decision instead of a routine monthly charge.", plan_fig)

    with col4:
        reg_df["ch"] = reg_df["registered_via"].apply(lambda x: f"Ch {int(x)}")
        reg_fig = px.bar(reg_df, x="ch", y="churn_pct", color="churn_pct", color_continuous_scale=ramp,
                         text=reg_df["churn_pct"].apply(lambda x: f"{x:.1f}%"),
                         labels={"churn_pct": "Churn (%)", "ch": ""})
        reg_fig.update_traces(textposition="outside", textfont=dict(size=12, color=INK),
                              hovertemplate="%{x}: %{y:.1f}% churn<extra></extra>")
        reg_fig.update_layout(coloraxis_showscale=False)
        spread = reg_df["churn_pct"].max() / max(reg_df["churn_pct"].min(), 0.01)
        chart_card("Acquisition", f"Sign-up channel matters: {spread:.0f}× gap, best to worst",
            "Channel IDs are anonymised sign-up pathways, and KKBox hasn't published the mapping. "
            "The difference in churn is still large and consistent.", reg_fig)

    st.write("")
    img_card("What the model learned",
        "Payment and subscription features dominate; listening barely registers",
        ASSETS_PATH / "shap_beeswarm.png",
        "Each dot is one user. Red means a high feature value, blue means low; dots to the right push the "
        "prediction towards churn. The top of the chart is expiry dates, pricing, cancellations and payment "
        "method. Listening behaviour sits near the bottom.", width_ratio=(1, 3, 1))

    ratio_total = ov["rev_ch"] / ov["rev_ret"] if ov["rev_ret"] else 0
    ratio_day   = per_day.get(1, 0) / per_day.get(0, 1) if per_day.get(0, 0) else 0
    if ratio_day < 1.5:
        rev_line = (f"Per day of subscription it's TWD {per_day.get(1,0):.1f} vs {per_day.get(0,0):.1f}, so most of "
                    "that gap comes from plan length, not from churners paying more for the same thing.")
    else:
        rev_line = (f"Even per day of subscription the gap holds (TWD {per_day.get(1,0):.1f} vs {per_day.get(0,0):.1f}), "
                    "so churners really are the higher-paying users.")
    st.markdown(f"""
    <div class='note'><b>A number worth reading carefully:</b> churned users' last payment averaged
      TWD {ov['rev_ch']:,.0f} vs TWD {ov['rev_ret']:,.0f} for retained users ({ratio_total:.1f}×). {rev_line}</div>
    """, unsafe_allow_html=True)

# ================================================================ 02 RETENTION
elif page == NAV[2]:
    avg_r = cohort["retention_rate"].mean()
    best  = cohort.loc[cohort["retention_rate"].idxmax()]
    page_header("02", "Retention", "Retention holds steady over time.",
        "Each bar is one month of new sign-ups, showing the share of that cohort that didn't churn. "
        "Split into two panels so every cohort stays readable.")

    mid = len(cohort) // 2
    def cohort_fig(df_s):
        f = px.bar(df_s, x="retention_rate", y="cohort", orientation="h", color="retention_rate",
                   color_continuous_scale=[[0, ACCENT], [0.45, GREY], [1, INK]],
                   text=df_s["retention_rate"].apply(lambda x: f"{x:.1f}%"),
                   labels={"retention_rate": "Retention (%)", "cohort": ""}, custom_data=["cohort_size"])
        f.update_traces(textposition="outside", textfont=dict(size=11, color=INK),
                        hovertemplate="%{y}: %{x:.1f}% retained<br>%{customdata[0]:,} users<extra></extra>")
        f.update_layout(coloraxis_showscale=False, xaxis_range=[80, 103],
                        yaxis={"categoryorder": "category ascending"})
        return f

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        chart_card("Recent", "Most recent cohorts", "The later half of sign-up months.",
                   cohort_fig(cohort.iloc[mid:]), 480)
    with c2:
        chart_card("Earlier", "Earlier cohorts", "January 2015 to the midpoint.",
                   cohort_fig(cohort.iloc[:mid]), 480)

    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Average retention", f"{avg_r:.1f}%")
    m2.metric("Best cohort", str(best["cohort"]), f"{best['retention_rate']:.1f}%")
    m3.metric("Cohorts tracked", str(len(cohort)))
    st.markdown("<div class='note'><b>So what?</b> Retention hasn't meaningfully declined across cohorts, "
                "so this isn't a story about the product getting worse. That points the investigation back to "
                "how people pay.</div>", unsafe_allow_html=True)

# ================================================================ 03 WHO TO SAVE
elif page == NAV[3]:
    page_header("03", "Who to save", "One clear priority.",
        f"The model gives each of the {n_scored:,} users in the hold-out set a churn probability, then sorts them "
        "into three tiers. High Risk users are the most likely to leave and carry the most revenue at stake.")

    cols = st.columns(3, gap="medium")
    for col, (_, row) in zip(cols, risk_df.iterrows()):
        clr = TIER_C.get(row["risk_tier"], MUTED)
        with col:
            st.markdown(f"""
            <div class='fade' style='background:{CARD};border:1px solid {LINE};border-radius:20px;padding:24px 26px'>
              <div style='display:flex;align-items:center;gap:8px'>
                <span style='width:9px;height:9px;border-radius:50%;background:{clr};display:inline-block'></span>
                <span class='mono'>{row['risk_tier']}</span>
              </div>
              <div style='font-family:Inter Tight;font-size:44px;font-weight:800;letter-spacing:-.03em;
                          color:{ACCENT if row['risk_tier']=='High Risk' else INK};line-height:1;margin:16px 0 4px'>
                {int(row['users']):,}</div>
              <div style='font-size:13px;color:{MUTED};margin-bottom:16px'>users</div>
              <div class='rule'></div>
              <div style='font-size:13px;color:{BODY};line-height:2'>
                Avg churn probability <b style='color:{INK}'>{row['avg_prob']}%</b><br>
                Revenue at risk <b style='color:{INK}'>TWD {row['rev_at_risk']:,.0f}</b>
              </div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    tiers = risk_df["risk_tier"].tolist()
    clrs  = [TIER_C.get(t, MUTED) for t in tiers]
    rc1, rc2 = st.columns(2, gap="medium")
    with rc1:
        f5 = go.Figure(go.Bar(x=tiers, y=risk_df["users"], marker_color=clrs, width=0.5,
                              text=[f"{v:,}" for v in risk_df["users"]], textposition="outside",
                              textfont=dict(color=INK, size=13), hovertemplate="%{x}: %{y:,} users<extra></extra>"))
        f5.update_layout(yaxis_title="Users", showlegend=False)
        chart_card("Distribution", "Users per risk tier", "High Risk users are a small slice of the base.", f5)
    with rc2:
        f6 = go.Figure(go.Bar(x=tiers, y=risk_df["rev_at_risk"], marker_color=clrs, width=0.5,
                              text=[f"TWD {v:,.0f}" for v in risk_df["rev_at_risk"]], textposition="outside",
                              textfont=dict(color=INK, size=12), hovertemplate="%{x}: TWD %{y:,.0f}<extra></extra>"))
        f6.update_layout(yaxis_title="TWD", showlegend=False)
        chart_card("Impact", "Revenue at risk per tier",
                   "...but they hold the largest share of revenue at stake.", f6, tag_color=ACCENT)

    st.markdown(f"<div class='note note-accent'><b>Where to act first:</b> the {n_high:,} High Risk users combine "
                "the highest churn probability with the most revenue at stake. The simulator shows what an offer "
                "aimed at them would cost and return.</div>", unsafe_allow_html=True)
    st.button("Open the simulator  →", type="primary", on_click=goto, args=(NAV[4],))

    top_risk = q("""
        WITH ranked_risk AS (
            SELECT risk_tier, churn_probability, plan_list_price,
                   ROUND(churn_probability * plan_list_price, 0) AS revenue_at_stake,
                   ROW_NUMBER() OVER (PARTITION BY risk_tier
                                      ORDER BY churn_probability * plan_list_price DESC) AS rank_in_tier
            FROM risk_scores)
        SELECT risk_tier, churn_probability, plan_list_price, revenue_at_stake, rank_in_tier
        FROM ranked_risk WHERE rank_in_tier <= 10 ORDER BY risk_tier, rank_in_tier
    """)
    st.markdown("<div style='height:28px'></div><span class='mono'>Intervention shortlist</span>"
                "<div class='card-hed' style='font-size:24px;margin:8px 0 6px'>Top 10 users to prioritise, per tier</div>"
                f"<div class='page-dek' style='margin-bottom:16px'>Ranked within each tier by revenue at stake "
                "(churn probability × plan price), not just the tier bucket.</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.dataframe(top_risk.style.format({"churn_probability": "{:.1%}", "plan_list_price": "TWD {:.0f}",
                                            "revenue_at_stake": "TWD {:.0f}"}),
                     width="stretch", hide_index=True)

# ================================================================ 04 SIMULATOR
elif page == NAV[4]:
    page_header("04", "Simulator", "Would an auto-renew offer<br>pay for itself?",
        "The offer: a discount for anyone who switches auto-renew on. Pick who receives it, how generous it is, "
        "and how many would-be churners you expect to take it. Defaults match the original analysis: "
        "High Risk users, 10% off, 30% uptake.")

    with st.container(border=True):
        cA, cB, cC = st.columns([1.3, 1, 1], gap="large")
        with cA:
            tiers_sel = st.multiselect("Who receives the offer", ["High Risk", "Medium Risk", "Low Risk"],
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
        pays       = roi_x >= 1
        verdict    = (f"That's <span style='background:{INK};color:{CARD};padding:0 10px;border-radius:999px'>"
                      f"{roi_x:.1f}× back</span> on every TWD spent." if pays else
                      f"That <span style='background:{ACCENT};color:{CARD};padding:0 10px;border-radius:999px'>"
                      f"loses money</span>: {roi_x:.2f}× back per TWD spent.")

        st.markdown(f"""
        <div class='fade' style='background:{CARD if pays else ACCENT_SOFT};border:1px solid {LINE if pays else "#FFC9B8"};
                    border-radius:24px;padding:32px 36px;margin:20px 0'>
          <span class='mono'>The verdict</span>
          <div style='font-family:Inter Tight;font-size:clamp(1.4rem,2.4vw,2rem);font-weight:700;line-height:1.35;
                      letter-spacing:-.02em;color:{INK};margin-top:10px'>
            Offering {disc}% off to {n_t:,} {who} users costs TWD {cost:,.0f} and keeps an estimated
            {users_kept:,.0f} subscribers, protecting TWD {saved:,.0f}. {verdict}
          </div>
        </div>""", unsafe_allow_html=True)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Users targeted", f"{n_t:,}")
        s2.metric("Campaign cost", f"TWD {cost:,.0f}")
        s3.metric("Revenue protected", f"TWD {saved:,.0f}")
        s4.metric("Return on spend", f"{roi_x:.1f}×", delta="pays for itself" if pays else "loses money",
                  delta_color="normal" if pays else "inverse")

        st.write("")
        order = ["High Risk", "Medium Risk", "Low Risk"]
        ta = tier_agg.set_index("risk_tier").reindex(order).dropna()
        roi_by_tier = ta["p"] * (conv / 100) / (disc / 100)
        colors = [(ACCENT if v < 1 else INK) if t in tiers_sel else FAINT
                  for t, v in zip(roi_by_tier.index, roi_by_tier.values)]
        patterns = ["" if t in tiers_sel else "/" for t in roi_by_tier.index]
        rf = go.Figure(go.Bar(
            x=roi_by_tier.index.tolist(), y=roi_by_tier.values, width=0.5,
            marker=dict(color=colors, pattern=dict(shape=patterns, fgcolor=GREY, size=8, solidity=0.25)),
            text=[f"{v:.1f}×" if v >= 0.1 else f"{v:.2f}×" for v in roi_by_tier.values],
            textposition="outside", textfont=dict(color=INK, size=13),
            hovertemplate="%{x}: %{y:.2f}× return<extra></extra>"))
        rf.add_hline(y=1, line_dash="dash", line_color=MUTED,
                     annotation_text="break-even", annotation_font_color=MUTED)
        rf.update_layout(showlegend=False, yaxis_title="Return per TWD spent",
                         yaxis_range=[0, max(roi_by_tier.max() * 1.25, 1.3)])
        chart_card("Why targeting matters", "Return per tier at these settings",
            "Price cancels out, so each tier's return is its churn probability × uptake ÷ discount. The same offer "
            "that pays off for High Risk users loses money on Low Risk ones, because most of them were never going "
            "to leave. Solid bars are the tiers you selected; orange means that tier loses money.", rf, 320)

        st.markdown(f"<div style='font-size:12.5px;color:{MUTED};line-height:1.7;margin-top:14px'>"
                    "Assumptions: everyone targeted gets the discount on one plan period; uptake applies to users who "
                    "would otherwise churn; saved revenue counts one plan period per retained user. Uptake is the "
                    "biggest unknown. A real rollout would test it on a small holdout group first, with churn among "
                    "non-targeted users as the guardrail metric.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div><span class='mono'>Recommendations</span>"
                "<div class='rule' style='margin-top:12px'></div>", unsafe_allow_html=True)
    recs = [
        ("01", "Give users a reason to turn auto-renew on",
         f"Users with auto-renew off churn at {gap_x:.0f}× the rate of those with it on, despite listening just as much. "
         "They haven't stopped valuing the product; they just haven't committed to renewing.",
         f"Offer a discount for switching auto-renew on, starting with the {n_high:,} High Risk users. At 10% off and "
         f"30% uptake, the model estimates a {roi['roi_ratio']}× return. Test the uptake assumption before scaling."),
        ("02", "Treat plan expiry as a moment to win users back",
         "Churn varies sharply by plan length, and expiry timing is one of the model's strongest signals. For users "
         "paying upfront, renewal is a single, deliberate decision rather than a routine charge.",
         "Test a nudge shortly before long plans expire: offer auto-renew or a monthly option instead of letting "
         "the plan simply run out."),
        ("03", "Audit acquisition channel spend",
         "The worst sign-up channel produces users who churn many times more often than the best one, and channel "
         "ranks among the model's meaningful predictors.",
         "Map the anonymised channel IDs to real channels, shift spend away from high-churn ones, and reinvest "
         "where users stay, even if upfront volume is lower."),
    ]
    for num, title, finding, action in recs:
        c0, c1 = st.columns([0.5, 7.5])
        c0.markdown(f"<div class='chap-num'>{num}</div>", unsafe_allow_html=True)
        c1.markdown(f"""
        <div class='chap-hed' style='margin-bottom:10px'>{title}</div>
        <div style='font-size:14px;color:{BODY};line-height:1.8'>
          <b style='color:{INK}'>Finding.</b> {finding}<br><b style='color:{INK}'>Action.</b> {action}
        </div>""", unsafe_allow_html=True)
        st.markdown("<div class='rule' style='margin:20px 0'></div>", unsafe_allow_html=True)

# ================================================================ 05 MODEL CHECKS
elif page == NAV[5]:
    tc = threshold_curve()
    best_row = tc.loc[tc.f1.idxmax()]
    f1_default = float(tc.loc[(tc.threshold - 0.5).abs().idxmin(), "f1"])

    page_header("05", "Model checks", "Can the model be trusted?",
        "An XGBoost classifier scores each user's churn risk. These checks show it beats a simple baseline, "
        "holds up across different data splits, and uses a threshold tuned for the job.")

    st.markdown(f"""
    <div class='grid4 fade'>
      <div class='stat-card' style='display:block'><div class='stat-num'>0.9876</div><div class='stat-lbl'>Hold-out AUC, on unseen data</div></div>
      <div class='stat-card' style='display:block'><div class='stat-num'>0.9875</div><div class='stat-lbl'>5-fold CV mean, no sign of overfitting</div></div>
      <div class='stat-card' style='display:block'><div class='stat-num'>±0.0003</div><div class='stat-lbl'>CV std deviation, very stable</div></div>
      <div class='stat-card' style='display:block'><div class='stat-num'>{best_row.f1:.3f}</div><div class='stat-lbl'>Best F1, at threshold {best_row.threshold:.2f}</div></div>
    </div><div style='height:22px'></div>
    """, unsafe_allow_html=True)

    mv1, mv2 = st.columns(2, gap="medium")
    with mv1:
        mc = go.Figure(go.Bar(x=["Logistic Regression (baseline)", "XGBoost"], y=[0.9028, 0.9876],
                              marker_color=[GREY, INK], width=0.45, text=["0.9028", "0.9876"],
                              textposition="outside", textfont=dict(color=INK, size=14),
                              hovertemplate="%{x}: AUC %{y:.4f}<extra></extra>"))
        mc.add_hline(y=0.5, line_dash="dot", line_color=MUTED,
                     annotation_text="random guessing", annotation_font_color=MUTED)
        mc.update_layout(yaxis_title="ROC-AUC", yaxis_range=[0.4, 1.05], showlegend=False)
        chart_card("Baseline comparison", "XGBoost beats the baseline by +0.085 AUC",
            "A simple linear model already does well (0.9028). The jump to 0.9876 shows there are non-linear "
            "patterns in subscription behaviour that justify the more complex model.", mc)
    with mv2:
        folds = [0.9873, 0.9875, 0.9873, 0.9871, 0.9880]
        cvf = go.Figure(go.Bar(x=[f"Fold {i}" for i in range(1, 6)], y=folds, width=0.45,
                               marker_color=[INK if s >= np.mean(folds) else GREY for s in folds],
                               text=[f"{s:.4f}" for s in folds], textposition="outside",
                               textfont=dict(color=INK, size=12), hovertemplate="%{x}: AUC %{y:.4f}<extra></extra>"))
        cvf.add_hline(y=float(np.mean(folds)), line_dash="dash", line_color=MUTED,
                      annotation_text=f"mean {np.mean(folds):.4f}", annotation_font_color=MUTED)
        cvf.update_layout(yaxis_title="ROC-AUC (zoomed)", yaxis_range=[0.985, 0.9895], showlegend=False)
        chart_card("Cross-validation", "The score holds across all 5 folds",
            "Every fold lands between 0.9871 and 0.9880. The axis is zoomed in to make the differences visible "
            "at all; this isn't a lucky train/test split.", cvf)

    st.write("")
    mv3, mv4 = st.columns(2, gap="medium")
    with mv3:
        th = go.Figure()
        th.add_scatter(x=tc.threshold, y=tc.f1, mode="lines", name="F1", line=dict(color=INK, width=3),
                       hovertemplate="threshold %{x:.2f}: F1 %{y:.3f}<extra></extra>")
        th.add_scatter(x=tc.threshold, y=tc.precision, mode="lines", name="Precision",
                       line=dict(color=MUTED, width=1.5, dash="dot"),
                       hovertemplate="threshold %{x:.2f}: precision %{y:.3f}<extra></extra>")
        th.add_scatter(x=tc.threshold, y=tc.recall, mode="lines", name="Recall",
                       line=dict(color=GREY, width=1.5, dash="dash"),
                       hovertemplate="threshold %{x:.2f}: recall %{y:.3f}<extra></extra>")
        th.add_vline(x=0.5, line_dash="dash", line_color=GREY,
                     annotation_text="default 0.5", annotation_font_color=MUTED)
        th.add_vline(x=float(best_row.threshold), line_color=INK,
                     annotation_text=f"best {best_row.threshold:.2f}", annotation_font_color=INK,
                     annotation_position="top left")
        th.update_layout(xaxis_title="Classification threshold", yaxis_range=[0, 1.05],
                         legend=dict(orientation="h", y=-0.25))
        chart_card("Threshold tuning", "The default threshold leaves performance on the table",
            f"At 0.5, F1 is {f1_default:.3f}. Raising the threshold to {best_row.threshold:.2f} lifts it to "
            f"{best_row.f1:.3f} by cutting false alarms while still catching most churners. "
            "Recomputed live from the hold-out predictions.", th)
    with mv4:
        img_card("Deep dive", "How auto-renew moves individual predictions",
            ASSETS_PATH / "shap_dependence_autorenew.png",
            "Auto-renew is binary: 0 is off, 1 is on. With it off, the model consistently pushes churn probability "
            "up, which is why it's the most actionable single lever.")

# ---------------------------------------------------------------- footer
st.markdown(f"""
<div style='margin-top:56px;padding-top:18px;border-top:1px solid {LINE};display:flex;
            justify-content:space-between;flex-wrap:wrap;gap:8px'>
  <span class='mono'>WSDM KKBox churn dataset · XGBoost AUC 0.9876 · 5-fold CV 0.9875 ±0.0003</span>
  <span class='mono'>Built by Akanksha Nayak</span>
</div>
""", unsafe_allow_html=True)
