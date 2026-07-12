# kkbox-subscription-retention-analysis

Retention analysis on 970,000+ subscribers of KKBox, Asia's leading music 
streaming platform — built to answer: **who is leaving, why, and who do we 
act on first?**

🔗 **[Live Dashboard](https://kkbox-subscription-retention-analysis-lxakz4zp4xegizha4x5jbq.streamlit.app/)**

---

## Key Findings
- Churned users paid **3× more** than retained users — promotional long plans attract disloyal users
- Auto-renew OFF users churn at **30.6% vs 3.8%** — an 8× difference, the strongest signal in the data
- Churn is a **payments problem, not an engagement problem** — churned users listened just as much

## Model Performance
- **Hold-out AUC: 0.9876** · 5-fold CV mean **0.9875 ± 0.0003** (stable across all folds, range 0.9871–0.9880)
- Beats a Logistic Regression baseline (AUC 0.9028) by +0.085
- Optimal decision threshold 0.85 → F1 0.849 (vs. 0.729 at default 0.5)
- Modelled **2.8x ROI** on a targeted retention campaign for high-risk users

## Stack
Python · SQL · XGBoost · SHAP · Streamlit

## Data
WSDM KKBox Churn Prediction Dataset — 970K users, 21.5M transactions, 
30M listening logs. Processed in Kaggle cloud environment due to ~8GB size.
