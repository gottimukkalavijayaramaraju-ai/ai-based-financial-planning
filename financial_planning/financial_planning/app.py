"""Streamlit UI.  Run with:  streamlit run app.py"""
import pandas as pd
import streamlit as st
import planner as pl

st.set_page_config(page_title="AI Financial Planning", page_icon="📈")
st.title("📈 AI-Based Financial Planning")
st.caption("Educational demo. Returns are assumptions, not guarantees. Not financial advice.")

tab1, tab2, tab3, tab4 = st.tabs(["Goal Planner", "Retirement", "Expense Forecast", "Health & Allocation"])

# ---- Goal planner
with tab1:
    c1, c2 = st.columns(2)
    goal = c1.number_input("Goal cost today", 10000, 100000000, 2000000, 50000)
    years = c1.slider("Years to goal", 1, 40, 10)
    saved = c1.number_input("Already saved for this goal", 0, 100000000, 100000, 10000)
    infl = c2.slider("Inflation % per year", 0.0, 12.0, 6.0, 0.5)
    ret = c2.slider("Expected return % per year", 1.0, 20.0, 11.0, 0.5)
    r = pl.required_sip(goal, years, infl, ret, saved)
    st.metric("Goal cost in future money", f"{r['target']:,.0f}")
    st.metric("Monthly SIP needed", f"{r['sip']:,.0f}")
    st.line_chart(pl.growth_table(r["sip"], ret, years, saved))

# ---- Retirement
with tab2:
    c1, c2 = st.columns(2)
    age = c1.number_input("Current age", 18, 70, 30)
    ra = c1.number_input("Retirement age", 40, 75, 60)
    le = c1.number_input("Life expectancy", 60, 100, 85)
    exp = c1.number_input("Current monthly expenses", 5000, 1000000, 40000, 1000)
    inf2 = c2.slider("Inflation %", 0.0, 12.0, 6.0, 0.5, key="inf2")
    pre = c2.slider("Return before retirement %", 1.0, 20.0, 11.0, 0.5)
    post = c2.slider("Return after retirement %", 1.0, 12.0, 7.0, 0.5)
    corp = c2.number_input("Current retirement corpus", 0, 100000000, 300000, 10000)
    sip = c2.number_input("Current monthly SIP", 0, 1000000, 10000, 1000)
    if ra > age and le > ra:
        p = pl.retirement_plan(age, ra, le, exp, inf2, pre, post, corp, sip)
        st.metric("Monthly expense at retirement", f"{p['expense_at_retirement_monthly']:,.0f}")
        st.metric("Corpus needed", f"{p['corpus_needed']:,.0f}")
        st.metric("Projected corpus", f"{p['projected_corpus']:,.0f}")
        if p["on_track"]:
            st.success("You are on track.")
        else:
            st.error(f"Shortfall {p['gap']:,.0f}. Add about {p['extra_sip_needed']:,.0f}/month to your SIP.")
    else:
        st.warning("Check your ages.")

# ---- Forecast
with tab3:
    st.write("Enter your last months of expenses (comma separated) or use sample data.")
    txt = st.text_area("Monthly expenses", ", ".join(str(int(x)) for x in pl.sample_history()))
    try:
        hist = [float(x) for x in txt.split(",") if x.strip()]
        if len(hist) < 6:
            st.warning("Enter at least 6 months.")
        else:
            horizon = st.slider("Months to forecast", 1, 12, 6)
            fc = pl.forecast_expenses(hist, horizon)
            st.line_chart(pd.concat([pd.Series(hist, name="Actual").reset_index(drop=True),
                                     fc["Forecast"].reset_index(drop=True).rename("Forecast")
                                     .set_axis(range(len(hist), len(hist) + horizon))], axis=1))
            st.dataframe(fc)
    except ValueError:
        st.error("Use numbers separated by commas.")

# ---- Health & allocation
with tab4:
    c1, c2 = st.columns(2)
    inc = c1.number_input("Monthly income", 1000, 5000000, 80000, 5000)
    ex = c1.number_input("Monthly expenses", 0, 5000000, 40000, 1000)
    emi = c1.number_input("Monthly EMIs", 0, 5000000, 10000, 1000)
    bal = c2.number_input("Savings balance", 0, 100000000, 150000, 10000)
    ins = c2.checkbox("I have term + health insurance")
    age3 = c2.number_input("Your age", 18, 80, 30, key="age3")
    risk = c2.selectbox("Risk appetite", ["Low", "Medium", "High"], index=1)
    h = pl.health_score(inc, ex, emi, bal, ins)
    st.subheader(f"Financial health: {h['score']}/100 ({h['grade']})")
    st.bar_chart(pd.Series(h["breakdown"], name="Points"))
    for t in h["tips"]:
        st.write("•", t)
    ef = pl.emergency_fund_target(ex)
    st.write(f"**Emergency fund target:** {ef['amount']:,.0f} ({ef['months']} months of expenses)")
    st.write("**Suggested allocation (%)**")
    st.bar_chart(pd.Series(pl.recommend_allocation(age3, risk)))
