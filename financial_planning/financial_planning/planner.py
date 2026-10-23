"""Core logic for AI-Based Financial Planning.

Modules:
  1. Goal planner          - SIP maths with inflation
  2. Retirement planner    - corpus needed vs. projected
  3. Expense forecasting   - machine learning (Linear Regression)
  4. Allocation + health   - rule-based advice and a 0-100 health score
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


# ------------------------------------------------------------ 1. GOAL PLANNER
def inflate(amount, inflation_pct, years):
    """Future cost of something that costs `amount` today."""
    return amount * (1 + inflation_pct / 100) ** years


def fv_sip(monthly, annual_return_pct, years):
    """Future value of a monthly SIP (investment at start of each month)."""
    i, n = annual_return_pct / 1200, int(years * 12)
    if i == 0:
        return monthly * n
    return monthly * (((1 + i) ** n - 1) / i) * (1 + i)


def required_sip(goal_today, years, inflation_pct, annual_return_pct, current_savings=0):
    """Monthly SIP needed to reach an inflation-adjusted goal."""
    target = inflate(goal_today, inflation_pct, years)
    gap = target - current_savings * (1 + annual_return_pct / 100) ** years
    if gap <= 0:
        return {"target": target, "sip": 0.0}
    return {"target": target, "sip": gap / fv_sip(1, annual_return_pct, years)}


def growth_table(monthly, annual_return_pct, years, current_savings=0):
    """Year-by-year corpus, handy for charts."""
    rows = []
    for y in range(0, int(years) + 1):
        value = current_savings * (1 + annual_return_pct / 100) ** y + fv_sip(monthly, annual_return_pct, y)
        rows.append({"Year": y, "Corpus": round(value)})
    return pd.DataFrame(rows).set_index("Year")


# --------------------------------------------------------- 2. RETIREMENT PLAN
def retirement_plan(age, retire_age, life_expectancy, monthly_expense,
                    inflation_pct, pre_return_pct, post_return_pct,
                    current_corpus, monthly_sip):
    years_to_go = retire_age - age
    years_in_ret = life_expectancy - retire_age

    expense_at_ret = inflate(monthly_expense * 12, inflation_pct, years_to_go)
    real = (1 + post_return_pct / 100) / (1 + inflation_pct / 100) - 1
    corpus_needed = (expense_at_ret * years_in_ret if abs(real) < 1e-9
                     else expense_at_ret * (1 - (1 + real) ** -years_in_ret) / real)

    projected = (current_corpus * (1 + pre_return_pct / 100) ** years_to_go
                 + fv_sip(monthly_sip, pre_return_pct, years_to_go))
    gap = corpus_needed - projected
    extra_sip = gap / fv_sip(1, pre_return_pct, years_to_go) if gap > 0 else 0.0
    return {"expense_at_retirement_monthly": expense_at_ret / 12,
            "corpus_needed": corpus_needed, "projected_corpus": projected,
            "gap": gap, "extra_sip_needed": extra_sip,
            "on_track": gap <= 0}


# ------------------------------------------------------- 3. EXPENSE FORECAST
def sample_history(months=24, seed=1):
    """Fake monthly expense history (replace with the user's own data)."""
    rng = np.random.default_rng(seed)
    t = np.arange(months)
    return list(np.round(30000 + 350 * t + 2500 * np.sin(t / 12 * 2 * np.pi)
                         + rng.normal(0, 1200, months)))


def forecast_expenses(history, horizon=6):
    """Fit a Linear Regression on month index and predict the next `horizon` months."""
    y = np.array(history, dtype=float)
    X = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    resid_std = float(np.std(y - model.predict(X)))
    future = np.arange(len(y), len(y) + horizon).reshape(-1, 1)
    pred = model.predict(future)
    return pd.DataFrame({"Forecast": pred.round(),
                         "Low": (pred - 1.96 * resid_std).round(),
                         "High": (pred + 1.96 * resid_std).round()},
                        index=[f"Month +{i}" for i in range(1, horizon + 1)])


# ------------------------------------------ 4. ALLOCATION + HEALTH SCORE
def recommend_allocation(age, risk):
    """risk: 'Low' | 'Medium' | 'High'. Classic 'equity = 100 - age', tilted by risk."""
    equity = 100 - age + {"Low": -15, "Medium": 0, "High": 15}[risk]
    equity = int(min(max(equity, 10), 90))
    gold = 5 if equity < 80 else 0
    cash = 5
    debt = 100 - equity - gold - cash
    return {"Equity": equity, "Debt": debt, "Gold": gold, "Cash": cash}


def emergency_fund_target(monthly_expense, dependents=0, stable_job=True):
    months = (6 if stable_job else 9) + min(dependents, 3)
    return {"months": months, "amount": months * monthly_expense}


def health_score(income, expenses, emi, savings_balance, insured):
    """Score out of 100 from four simple checks."""
    savings_rate = (income - expenses - emi) / income
    dti = emi / income
    ef_months = savings_balance / expenses if expenses else 0
    parts = {
        "Savings rate": min(max(savings_rate / 0.20, 0), 1) * 30,
        "Debt burden": min(max((0.5 - dti) / 0.5, 0), 1) * 25,
        "Emergency fund": min(ef_months / 6, 1) * 30,
        "Insurance": 15 if insured else 0,
    }
    total = round(sum(parts.values()))
    grade = "Excellent" if total >= 80 else "Good" if total >= 60 else "Needs work"
    tips = []
    if savings_rate < 0.20: tips.append("Aim to save at least 20% of income.")
    if dti > 0.35: tips.append("EMIs are heavy; avoid new loans and prepay the costliest one.")
    if ef_months < 6: tips.append(f"Emergency fund covers {ef_months:.1f} months; build it to 6.")
    if not insured: tips.append("Get term life and health insurance.")
    return {"score": total, "grade": grade,
            "breakdown": {k: round(v) for k, v in parts.items()},
            "tips": tips or ["Great position. Stay consistent."]}
